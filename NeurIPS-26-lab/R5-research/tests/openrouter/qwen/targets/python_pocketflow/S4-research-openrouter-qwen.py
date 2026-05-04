import os
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# =============================================================================
# SPL FUNCTION MAPPINGS (Prompt Builders)
# =============================================================================

# SPL: CREATE FUNCTION plan_queries(topic) RETURNS TEXT AS $$ ...
def _plan_queries_prompt(topic: str) -> str:
    return f"""You are a research planner. Generate 3 focused search queries to gather information on the topic: {topic}.
List each query on a new line prefixed with QUERY: """

# SPL: CREATE FUNCTION extract_facts(web_results) RETURNS TEXT AS $$ ...
def _extract_facts_prompt(web_results: str) -> str:
    return f"""Extract and summarize the key facts from the following web search results: {web_results}.
Return a concise bullet-point list of the most important findings. """

# SPL: CREATE FUNCTION assess_and_report(notes_data) RETURNS TEXT AS $$ ...
def _assess_and_report_prompt(notes_data: str) -> str:
    return f"""Synthesize the following aggregated notes into a comprehensive final report: {notes_data}.
Ensure all key findings are clearly structured and actionable. """

# =============================================================================
# EXTERNAL SERVICES (LLM, Web, I/O) - ETL Steps
# =============================================================================

def _llm_generate(prompt: str, model: str = None) -> str:
    model = model or os.environ.get("LLM_MODEL", "qwen/qwen3.6-plus")
    """
    SPL: GENERATE <function>(args) INTO <var>
    Calls OpenRouter API for Qwen model. Falls back to mock if no API key.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        logging.warning("OPENROUTER_API_KEY not set. Returning mock LLM response.")
        return f"[Mock LLM Output]\n{prompt[:80]}...\n[End Mock]"

    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost/splc",
            "X-Title": "SPL-Compiler-Output"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("choices", [{}])[0].get("message", {}).get("content", "No content")
    except Exception as e:
        logging.error(f"LLM API Error: {e}. Fallback to mock.")
        return f"[Fallback LLM Output]\n{prompt[:80]}...\n[End Fallback]"

def _search_web(queries: str, max_results: int = 5) -> str:
    """SPL: CALL search_web(@current_queries) INTO @web_results"""
    import re
    try:
        from ddgs import DDGS
    except ImportError:
        from duckduckgo_search import DDGS
    # Extract first QUERY: line if present
    m = re.search(r'QUERY:\s*(.+)', queries)
    query = m.group(1).strip() if m else queries.strip()
    logging.info(f"[ETL-EXTRACT] Web search: {query}")
    try:
        results = DDGS().text(query, max_results=max_results)
        if not results:
            return f"No results for: {query}"
        lines = []
        for i, r in enumerate(results, 1):
            lines.append(f"[{i}] {r.get('title', '')}\n    URL: {r.get('href', '')}\n    {r.get('body', '')}")
        return "\n\n".join(lines)
    except Exception as e:
        return f"Search error: {e}"

def _write_file(filepath: str, content: str) -> None:
    """
    SPL: CALL write_file("report.txt", @report)
    ETL-LOAD step: Persists final output to disk.
    """
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    logging.info(f"[ETL-LOAD] Successfully wrote {len(content)} characters to {filepath}")

# =============================================================================
# POCKETFLOW-STYLE WORKFLOW (Minimalist ETL Orchestration)
# =============================================================================

class S3ResearchOpenrouterQwenFlow:
    """
    PocketFlow-style ETL workflow orchestrator for S3-research-openrouter-qwen.
    Matches SPL: WORKFLOW research_workflow semantics.
    """
    def __init__(self):
        self.state: Dict[str, Any] = {}

    def run(self, topic: str = "default_topic") -> str:
        """
        SPL: INPUT @topic STRING := "default_topic"
        SPL: OUTPUT @report STRING
        """
        # SPL: @loop_count := 0; @iteration := 0; etc.
        self.state = {
            "topic": topic,
            "loop_count": 0,
            "iteration": 0,
            "notes": "",
            "current_queries": "",
            "web_results": "",
            "extracted_facts": "",
            "report": ""
        }

        logging.info(f"Starting workflow. Topic: {self.state['topic']}")

        # SPL: WHILE @loop_count < 2 AND @iteration < 3 DO
        while self.state["loop_count"] < 2 and self.state["iteration"] < 3:
            self.state["iteration"] += 1
            logging.info(f"[ITERATION] Step {self.state['iteration']} / {self.state['iteration']}")

            # SPL: GENERATE plan_queries(@topic) INTO @current_queries;
            prompt = _plan_queries_prompt(self.state["topic"])
            self.state["current_queries"] = _llm_generate(prompt)

            # SPL: CALL search_web(@current_queries) INTO @web_results;
            self.state["web_results"] = _search_web(self.state["current_queries"])

            # SPL: GENERATE extract_facts(@web_results) INTO @extracted_facts;
            prompt = _extract_facts_prompt(self.state["web_results"])
            self.state["extracted_facts"] = _llm_generate(prompt)

            # SPL: @notes := @notes + @extracted_facts;
            self.state["notes"] += f"\n--- Iteration {self.state['iteration']} ---\n{self.state['extracted_facts']}\n"

            # SPL: @loop_count := @loop_count + 1;
            self.state["loop_count"] += 1
            logging.info(f"[STATE] Notes length: {len(self.state['notes'])} chars")

        # SPL: GENERATE assess_and_report(@notes) INTO @report;
        prompt = _assess_and_report_prompt(self.state["notes"])
        self.state["report"] = _llm_generate(prompt)

        # SPL: CALL write_file("report.txt", @report);
        _write_file("report.txt", self.state["report"])

        # SPL: RETURN @report WITH status = "complete";
        logging.info("Workflow execution finished. Status: complete")
        return self.state["report"]


if __name__ == "__main__":
    # Initialize and run the PocketFlow-style ETL workflow
    workflow = S3ResearchOpenrouterQwenFlow()
    
    # SPL: WORKFLOW invocation with default INPUT
    final_report = workflow.run(topic="default_topic")
    
    print("\n" + "="*50)
    print("FINAL OUTPUT PREVIEW:")
    print(final_report[:300] + "..." if len(final_report) > 300 else final_report)
    print("="*50)