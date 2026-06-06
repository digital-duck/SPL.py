"""
s3_agent_claude_cli_claude.py
Compiled from S3-agent-claude_cli-claude.spl → Python / PocketFlow
"""
import re
import subprocess
import sys
from typing import Any

import yaml
from pocketflow import Flow, Node


# ── LLM backend (claude_cli adapter) ─────────────────────────────────────────

def call_llm(prompt: str) -> str:
    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


# ── Tool implementations ──────────────────────────────────────────────────────

# SPL: CALL parse_yaml(@raw_response) INTO @parse_result
def parse_yaml_tool(raw: str) -> dict:
    match = re.search(r"```yaml\s*(.*?)```", raw, re.DOTALL)
    if not match:
        return {"parse_error": f"no YAML fence found in: {raw[:200]}"}
    try:
        result = yaml.safe_load(match.group(1).strip())
        if not isinstance(result, dict):
            return {"parse_error": f"expected mapping, got {type(result).__name__}: {result}"}
        return result or {}
    except yaml.YAMLError as exc:
        return {"parse_error": str(exc)}


# SPL: CALL force_block_scalars(@raw_response) INTO @fixed_response
def force_block_scalars_tool(raw: str) -> str:
    fixed = re.sub(r':\s*"([^"]*)"', lambda m: f": {m.group(1)}", raw)
    fixed = re.sub(r":\s*'([^']*)'", lambda m: f": {m.group(1)}", fixed)
    return fixed


# SPL: CALL extract_field(@decision, 'search_query') INTO @search_query
def extract_field_tool(decision: dict, field: str) -> str:
    return str(decision.get(field, ""))


# SPL: CALL search_web(@search_query) INTO @search_results
# Replace this stub with a real search API (e.g. SerpAPI, Tavily, DuckDuckGo).
def search_web_tool(query: str) -> str:
    return f"[stub: search results for '{query}']"


# ── Prompt templates (SPL: CREATE FUNCTION … AS $$ … $$) ─────────────────────

# SPL: CREATE FUNCTION decide_action(question TEXT, context TEXT) RETURNS TEXT AS $$ … $$
DECIDE_ACTION_PROMPT = """\
You are a research agent. Given the question and accumulated search context, decide the next action.

Question: {question}
Context: {context}

Respond with a fenced YAML block:
```yaml
action: search
search_query: <your search query here>
```
or, if you have sufficient information to answer:
```yaml
action: answer
```"""

# SPL: CREATE FUNCTION answer_question(question TEXT, context TEXT) RETURNS TEXT AS $$ … $$
ANSWER_QUESTION_PROMPT = """\
Using the search context provided, synthesize a comprehensive prose answer to the question.

Question: {question}
Context: {context}"""


# ── Nodes ─────────────────────────────────────────────────────────────────────

class InitNode(Node):
    # SPL: @context := 'No previous search'; @iteration := 0; @done := 'false';
    def prep(self, shared: dict) -> None:
        return None

    def exec(self, _: Any) -> None:
        return None

    def post(self, shared: dict, prep_result: Any, exec_result: Any) -> str:
        shared.update(context="No previous search", iteration=0, done="false")
        return "loop_check"


class LoopCheckNode(Node):
    # SPL: WHILE @done != 'true' AND @iteration < 10 DO
    def prep(self, shared: dict) -> tuple:
        return shared["done"], shared["iteration"]

    def exec(self, args: tuple) -> bool:
        done, iteration = args
        return done != "true" and iteration < 10

    def post(self, shared: dict, prep_result: Any, exec_result: bool) -> str:
        return "continue" if exec_result else "exit"


class DecideActionNode(Node):
    # SPL: @iteration := @iteration + 1;
    #      GENERATE decide_action(@question, @context) INTO @raw_response;
    def prep(self, shared: dict) -> tuple:
        return shared["question"], shared["context"]

    def exec(self, args: tuple) -> str:
        question, context = args
        prompt = DECIDE_ACTION_PROMPT.format(question=question, context=context)
        return call_llm(prompt)

    def post(self, shared: dict, prep_result: Any, exec_result: str) -> str:
        shared["iteration"] += 1        # SPL: @iteration := @iteration + 1
        shared["raw_response"] = exec_result
        return "parse"


class ParseYamlNode(Node):
    # SPL: CALL parse_yaml(@raw_response) INTO @parse_result;
    def prep(self, shared: dict) -> str:
        return shared["raw_response"]

    def exec(self, raw: str) -> dict:
        return parse_yaml_tool(raw)

    def post(self, shared: dict, prep_result: Any, exec_result: dict) -> str:
        shared["parse_result"] = exec_result
        # SPL: EVALUATE @parse_result WHEN contains('parse_error') THEN … ELSE @decision := @parse_result END
        if "parse_error" in exec_result:
            return "parse_error"
        shared["decision"] = exec_result
        return "evaluate"


class ForceBlockScalarsNode(Node):
    # SPL: CALL force_block_scalars(@raw_response) INTO @fixed_response;
    def prep(self, shared: dict) -> str:
        return shared["raw_response"]

    def exec(self, raw: str) -> str:
        return force_block_scalars_tool(raw)

    def post(self, shared: dict, prep_result: Any, exec_result: str) -> str:
        shared["fixed_response"] = exec_result
        return "retry_parse"


class RetryParseNode(Node):
    # SPL: CALL parse_yaml(@fixed_response) INTO @retry_result;
    def prep(self, shared: dict) -> str:
        return shared["fixed_response"]

    def exec(self, fixed: str) -> dict:
        return parse_yaml_tool(fixed)

    def post(self, shared: dict, prep_result: Any, exec_result: dict) -> str:
        shared["retry_result"] = exec_result
        # SPL: EVALUATE @retry_result WHEN contains('parse_error') THEN RETURN @retry_result WITH status='error'
        if "parse_error" in exec_result:
            shared["answer"] = str(exec_result)
            shared["status"] = "error"
            return "error"
        # SPL: ELSE @decision := @retry_result END
        shared["decision"] = exec_result
        return "evaluate"


class EvaluateDecisionNode(Node):
    # SPL: EVALUATE @decision WHEN contains('action: search') THEN … ELSE … END
    def prep(self, shared: dict) -> dict:
        return shared["decision"]

    def exec(self, decision: dict) -> str:
        return decision.get("action", "")

    def post(self, shared: dict, prep_result: Any, exec_result: str) -> str:
        return "search" if exec_result == "search" else "answer"


class SearchWebNode(Node):
    # SPL: CALL extract_field(@decision, 'search_query') INTO @search_query;
    #      CALL search_web(@search_query) INTO @search_results;
    #      @context := @context + '\nSEARCH: ' + @search_query + '\nRESULTS: ' + @search_results;
    def prep(self, shared: dict) -> tuple:
        return shared["decision"], shared["context"]

    def exec(self, args: tuple) -> tuple:
        decision, _ = args
        search_query = extract_field_tool(decision, "search_query")
        search_results = search_web_tool(search_query)
        return search_query, search_results

    def post(self, shared: dict, prep_result: Any, exec_result: tuple) -> str:
        _, context = prep_result
        search_query, search_results = exec_result
        shared["context"] = (
            context + f"\nSEARCH: {search_query}\nRESULTS: {search_results}"
        )
        return "loop_check"


class AnswerQuestionNode(Node):
    # SPL: GENERATE answer_question(@question, @context) INTO @answer;
    #      @done := 'true';
    #      RETURN @answer WITH status = 'complete';
    def prep(self, shared: dict) -> tuple:
        return shared["question"], shared["context"]

    def exec(self, args: tuple) -> str:
        question, context = args
        prompt = ANSWER_QUESTION_PROMPT.format(question=question, context=context)
        return call_llm(prompt)

    def post(self, shared: dict, prep_result: Any, exec_result: str) -> str:
        shared["answer"] = exec_result
        shared["done"] = "true"
        shared["status"] = "complete"
        return "done"   # terminal — no successor mapped → flow ends


# ── Flow assembly ─────────────────────────────────────────────────────────────

def build_flow() -> Flow:
    init            = InitNode()
    loop_check      = LoopCheckNode()
    decide_action   = DecideActionNode()
    parse_yaml_node = ParseYamlNode()
    force_block     = ForceBlockScalarsNode()
    retry_parse     = RetryParseNode()
    evaluate        = EvaluateDecisionNode()
    search_web      = SearchWebNode()
    answer_question = AnswerQuestionNode()

    # SPL: initialise → enter WHILE loop
    init          - "loop_check"  >> loop_check
    loop_check    - "continue"    >> decide_action
    # "exit" has no successor → flow terminates (max iterations reached)

    # SPL: GENERATE decide_action → CALL parse_yaml
    decide_action   - "parse"       >> parse_yaml_node

    # SPL: EVALUATE @parse_result WHEN contains('parse_error')
    parse_yaml_node - "parse_error" >> force_block
    parse_yaml_node - "evaluate"    >> evaluate

    # SPL: CALL force_block_scalars → retry CALL parse_yaml
    force_block     - "retry_parse" >> retry_parse
    # "error" has no successor → flow terminates (unrecoverable YAML parse failure)
    retry_parse     - "evaluate"    >> evaluate

    # SPL: EVALUATE @decision WHEN contains('action: search')
    evaluate        - "search"      >> search_web
    evaluate        - "answer"      >> answer_question

    # SPL: update @context → loop back
    search_web      - "loop_check"  >> loop_check
    # "done" has no successor → flow terminates (success)

    return Flow(start=init)


# ── Public API ────────────────────────────────────────────────────────────────

def run_web_search_agent(question: str) -> dict:
    """
    Mirrors: WORKFLOW web_search_agent INPUT @question TEXT OUTPUT @answer TEXT
    """
    shared: dict = {"question": question}
    build_flow().run(shared)
    return {
        "answer":     shared.get("answer", ""),
        "status":     shared.get("status", "max_iterations_reached"),
        "iterations": shared.get("iteration", 0),
    }


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is the speed of light?"
    result = run_web_search_agent(question)
    print(f"Status     : {result['status']}")
    print(f"Iterations : {result['iterations']}")
    print(f"\nAnswer:\n{result['answer']}")