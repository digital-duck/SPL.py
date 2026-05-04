import os
import json
import urllib.request
from typing import Dict, Any

# SPL: CREATE FUNCTION decide_action(query, context)
# RETURNS TEXT AS $$ Decide whether to 'search' or 'answer' based on query: {query} and context: {context}. Output YAML with an 'action' token and 'query' field. $$;
def prompt_decide_action(query: str, context: str) -> str:
    return f"Decide whether to 'search' or 'answer' based on query: {query} and context: {context}. Output YAML with an 'action' token and 'query' field."

# SPL: CREATE FUNCTION validate_yaml(raw)
# RETURNS TEXT AS $$ Check if the following text is valid YAML: {raw}. Return only 'valid' or 'malformed'. $$;
def prompt_validate_yaml(raw: str) -> str:
    return f"Check if the following text is valid YAML: {raw}. Return only 'valid' or 'malformed'."

# SPL: CREATE FUNCTION repair_output(bad_yaml)
# RETURNS TEXT AS $$ The following YAML is malformed. Repair it strictly into valid YAML: {bad_yaml} $$;
def prompt_repair_output(bad_yaml: str) -> str:
    return f"The following YAML is malformed. Repair it strictly into valid YAML: {bad_yaml}"

# SPL: CREATE FUNCTION extract_action(valid_yaml)
# RETURNS TEXT AS $$ Extract the 'action' value from the following valid YAML: {valid_yaml} $$;
def prompt_extract_action(valid_yaml: str) -> str:
    return f"Extract the 'action' value from the following valid YAML: {valid_yaml}"

# SPL: CREATE FUNCTION generate_final(state, query)
# RETURNS TEXT AS $$ Synthesize a comprehensive final answer using accumulated context: {state} to address the original query: {query} $$;
def prompt_generate_final(state: str, query: str) -> str:
    return f"Synthesize a comprehensive final answer using accumulated context: {state} to address the original query: {query}"

# SPL: GENERATE (LLM Invocation Layer for OpenRouter Qwen)
def generate(prompt: str, system: str = "You are a precise, structured assistant.") -> str:
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    model = os.getenv("LLM_MODEL", "qwen/qwen3.6-plus")
    if not api_key:
        return "[MOCK_LLM_RESPONSE]"
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        "temperature": 0.1
    }).encode("utf-8")
    
    req = urllib.request.Request(
        url, data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return json.loads(res.read().decode())["choices"][0]["message"]["content"].strip()
    except Exception:
        return "[LLM_CALL_FAILED]"

# SPL: CALL web_search(@user_query) INTO @search_results;
def web_search(query: str, max_results: int = 5) -> str:
    import re
    try:
        from ddgs import DDGS
    except ImportError:
        from duckduckgo_search import DDGS
    m = re.search(r'search_query:\s*(.+)', query)
    if m:
        query = m.group(1).strip().strip('"').strip("'")
    try:
        results = DDGS().text(query.strip(), max_results=max_results)
        if not results:
            return f"No results for: {query}"
        lines = []
        for i, r in enumerate(results, 1):
            lines.append(f"[{i}] {r.get('title', '')}\n    URL: {r.get('href', '')}\n    {r.get('body', '')}")
        return "\n\n".join(lines)
    except Exception as e:
        return f"Search error: {e}"

class S3AgentOpenRouterQwen:
    """
    SPL: WORKFLOW DecisionAgent
    INPUT @user_query STRING
    OUTPUT @final_response STRING
    """
    def run(self, user_query: str) -> Dict[str, Any]:
        # SPL: DO
        # SPL:   @shared_state := "";
        # SPL:   @iteration := 0;
        # SPL:   @done := false;
        ctx = {
            "@user_query": user_query,
            "@final_response": "",
            "@shared_state": "",
            "@iteration": 0,
            "@done": False
        }

        # SPL:   WHILE @done = false AND @iteration < 3 DO
        while not ctx["@done"] and ctx["@iteration"] < 3:
            # SPL:     GENERATE decide_action(@user_query, @shared_state) INTO @raw_yaml;
            ctx["@raw_yaml"] = generate(prompt_decide_action(ctx["@user_query"], ctx["@shared_state"]))

            # SPL:     @parse_valid := false;
            # SPL:     @parse_iter := 0;
            ctx["@parse_valid"] = False
            ctx["@parse_iter"] = 0

            # SPL:     WHILE @parse_valid = false AND @parse_iter < 3 DO
            while not ctx["@parse_valid"] and ctx["@parse_iter"] < 3:
                # SPL:       GENERATE validate_yaml(@raw_yaml) INTO @yaml_status;
                ctx["@yaml_status"] = generate(prompt_validate_yaml(ctx["@raw_yaml"]))

                # SPL:       EVALUATE @yaml_status WHEN contains("malformed") THEN
                if "malformed" in ctx["@yaml_status"].lower():
                    # SPL:         GENERATE repair_output(@raw_yaml) INTO @raw_yaml;
                    ctx["@raw_yaml"] = generate(prompt_repair_output(ctx["@raw_yaml"]))
                    # SPL:         @parse_iter := @parse_iter + 1;
                    ctx["@parse_iter"] += 1
                # SPL:       ELSE
                else:
                    # SPL:         @parse_valid := true;
                    ctx["@parse_valid"] = True
                # SPL:       END;
            # SPL:     END;

            # SPL:     GENERATE extract_action(@raw_yaml) INTO @action_token;
            ctx["@action_token"] = generate(prompt_extract_action(ctx["@raw_yaml"]))

            # SPL:     EVALUATE @action_token WHEN contains("search") THEN
            if "search" in ctx["@action_token"].lower():
                # SPL:       CALL web_search(@user_query) INTO @search_results;
                ctx["@search_results"] = web_search(ctx["@user_query"])
                # SPL:       @shared_state := @shared_state + " " + @search_results;
                ctx["@shared_state"] = ctx["@shared_state"] + " " + ctx["@search_results"]
                # SPL:       @iteration := @iteration + 1;
                ctx["@iteration"] += 1
            # SPL:     ELSE
            else:
                # SPL:       GENERATE generate_final(@shared_state, @user_query) INTO @final_response;
                ctx["@final_response"] = generate(prompt_generate_final(ctx["@shared_state"], ctx["@user_query"]))
                # SPL:       @done := true;
                ctx["@done"] = True
            # SPL:     END;
        # SPL:   END;

        # SPL:   RETURN @final_response WITH status = "complete";
        return {"status": "complete", "final_response": ctx["@final_response"]}

if __name__ == "__main__":
    agent = S3AgentOpenRouterQwen()
    # Example execution
    result = agent.run("What are the latest developments in quantum computing?")
    print(json.dumps(result, indent=2))