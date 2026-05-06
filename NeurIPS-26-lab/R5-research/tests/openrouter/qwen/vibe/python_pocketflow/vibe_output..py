import os
import re
import json
import time
import urllib.request
import urllib.parse
import concurrent.futures
import logging
from pathlib import Path

# ==========================================================
# PocketFlow: Minimalist ETL-style LLM Orchestration Engine
# ==========================================================
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("PocketFlow")

def call_llm(prompt: str, model: str = None) -> str:
    """Call an LLM via OpenAI-compatible API. Reads API key & model from env."""
    model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError("Set OPENAI_API_KEY or OPENROUTER_API_KEY environment variable.")

    is_openrouter = bool(os.getenv("OPENROUTER_API_KEY")) or model.startswith("openrouter/")
    url = "https://openrouter.ai/api/v1/chat/completions" if is_openrouter else "https://api.openai.com/v1/chat/completions"
    
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    if is_openrouter:
        headers.update({"HTTP-Referer": "http://localhost", "X-Title": "PocketFlowResearch"})

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        raise RuntimeError(f"LLM inference failed: {e}")

def search_web(query: str) -> str:
    """Fetch factual snippets via DuckDuckGo Instant Answer API."""
    url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        snippets = []
        if data.get("Abstract"):
            snippets.append(data["Abstract"])
        for rel in data.get("RelatedTopics", [])[:5]:
            txt = rel.get("Text", "")
            if txt: snippets.append(txt)
            if "Topics" in rel:
                for sub in rel.get("Topics", [])[:3]:
                    stxt = sub.get("Text", "")
                    if stxt: snippets.append(stxt)
        return "\n".join(snippets) if snippets else "No direct results found."
    except Exception as e:
        raise RuntimeError(f"Web search failed for '{query}': {e}")

def parse_yaml_block(text: str) -> dict:
    """Extract and parse a simple YAML/Markdown block into a dictionary."""
    text = re.sub(r"^```(?:yaml)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text.strip())
    result = {}
    current_key = None
    is_list = False
    for line in text.split("\n"):
        line_s = line.strip()
        if not line_s: continue
        if line_s.startswith("- "):
            if current_key:
                if not is_list:
                    result[current_key] = []
                    is_list = True
                result[current_key].append(line_s[2:].strip())
            continue
        if ":" in line_s:
            k, v = line_s.split(":", 1)
            k, v = k.strip(), v.strip()
            current_key = k
            is_list = False
            result[k] = v if v else []
    return result

# ==========================================================
# Node Definitions (ETL Stages)
# ==========================================================
class Node:
    def __init__(self, name: str): self.name = name
    def prep(self, ctx: dict): pass
    def exec(self, ctx: dict): raise NotImplementedError
    def post(self, ctx: dict) -> str | None: return None

class PlannerNode(Node):
    """GENERATE plan_queries"""
    def exec(self, ctx: dict):
        feedback = ctx.get("feedback", "")
        prompt = f"""You are a senior research planner. Topic: "{ctx['topic']}"
{f"Previous synthesis feedback: {feedback}" if feedback else "This is the initial planning phase."}
Generate exactly 3 diverse, targeted web search queries to comprehensively cover the topic.
Output STRICT YAML only:
queries:
  - "query 1"
  - "query 2"
  - "query 3"
"""
        raw = call_llm(prompt)
        parsed = parse_yaml_block(raw)
        queries = parsed.get("queries", [])
        ctx["current_queries"] = queries if isinstance(queries, list) else [parsed.get("queries")]
        log.info(f"Planner generated {len(ctx['current_queries'])} queries.")

    def post(self, ctx: dict) -> str: return "searcher"

class SearcherNode(Node):
    """CALL search_web -> GENERATE extract_facts (Map/Parallel)"""
    def exec(self, ctx: dict):
        queries = ctx.get("current_queries", [])
        def process_query(q: str) -> str:
            try:
                log.info(f"Searching: {q}")
                raw_results = search_web(q)
                extract_prompt = f"Query: {q}\nSearch result: {raw_results}\nExtract 3-5 concise, factual snippets strictly relevant to the query.\nFormat:\nQ: {q}\nFacts: <bullet points>"
                facts = call_llm(extract_prompt)
                return facts.strip()
            except Exception as e:
                log.error(f"Query failed: {e}")
                return f"Q: {q}\nFacts: [Error retrieving data]"

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(3, len(queries))) as ex:
            facts_list = list(ex.map(process_query, queries))
        ctx["notes"].extend(facts_list)
        log.info(f"Extracted {len(facts_list)} fact blocks into @notes buffer.")

    def post(self, ctx: dict) -> str: return "synthesizer"

class SynthesizerNode(Node):
    """EVALUATE @synthesis_action / CREATE FUNCTION assess_and_report"""
    def exec(self, ctx: dict):
        # Bypass LLM if max iterations reached
        if ctx.get("loop_count", 0) >= 2:
            ctx["synthesis_action"] = "finalize"
            ctx["feedback"] = "Max iterations reached. Forcing finalization."
            ctx["report_content"] = ""
            return

        notes_txt = "\n---\n".join(ctx.get("notes", []))
        prompt = f"""You are a research synthesizer evaluating completeness for: "{ctx['topic']}"
Accumulated notes:
{notes_txt}
Assess if the research is sufficient. Output STRICT YAML:
If gaps exist:
action: research
feedback: <describe specific missing angles or data points>
If complete:
action: finalize
content: <draft the comprehensive markdown report here>
"""
        raw = call_llm(prompt)
        parsed = parse_yaml_block(raw)
        ctx["synthesis_action"] = parsed.get("action", "finalize").lower()
        ctx["feedback"] = parsed.get("feedback", "")
        ctx["report_content"] = parsed.get("content", "")
        log.info(f"Synthesis action: {ctx['synthesis_action']}")

    def post(self, ctx: dict) -> str | None:
        action = ctx.get("synthesis_action", "finalize")
        if action == "research" and ctx.get("loop_count", 0) < 2:
            ctx["loop_count"] += 1
            log.info(f"Gap detected. Loop iteration {ctx['loop_count']}/2.")
            return "planner"
        ctx["loop_count"] = ctx.get("loop_count", 0)
        return "reporter"

class ReporterNode(Node):
    """RETURN @report WITH status=complete & file I/O"""
    def exec(self, ctx: dict):
        if not ctx.get("report_content"):
            notes_txt = "\n---\n".join(ctx.get("notes", []))
            prompt = f"""Synthesize the following research notes into a comprehensive, well-structured markdown report on "{ctx['topic']}".
Include: Title, Executive Summary, Key Findings, Detailed Analysis, Conclusions, and References/Notes section.
Notes:
{notes_txt}
"""
            ctx["report_content"] = call_llm(prompt)
        
        safe_topic = re.sub(r'[^\w\-]+', '_', ctx['topic'])[:40]
        filename = f"research_{safe_topic}.md"
        Path(filename).write_text(ctx["report_content"], encoding="utf-8")
        ctx["report"] = ctx["report_content"]
        ctx["status"] = "complete"
        log.info(f"Final report saved to {filename}")

    def post(self, ctx: dict) -> None: return None

# ==========================================================
# Flow Orchestrator
# ==========================================================
class PocketFlow:
    def __init__(self, nodes: dict, start_node: str, max_steps: int = 15):
        self.nodes = nodes
        self.start = start_node
        self.max_steps = max_steps
        self.ctx = {}

    def run(self, initial_ctx: dict = None) -> dict:
        self.ctx = initial_ctx or {}
        self.ctx.setdefault("notes", [])
        self.ctx.setdefault("loop_count", 0)
        current = self.start
        step = 0
        try:
            while current and step < self.max_steps:
                node = self.nodes.get(current)
                if not node:
                    raise RuntimeError(f"Node '{current}' not wired in flow.")
                log.info(f"▶ Executing: {current} (step {step+1})")
                node.prep(self.ctx)
                node.exec(self.ctx)
                current = node.post(self.ctx)
                step += 1
            return self.ctx
        except Exception as e:
            log.error(f"Workflow halted due to exception: {e}")
            self.ctx["status"] = "error"
            self.ctx["error"] = str(e)
            raise

def create_deep_research_flow() -> PocketFlow:
    planner = PlannerNode("planner")
    searcher = SearcherNode("searcher")
    synthesizer = SynthesizerNode("synthesizer")
    reporter = ReporterNode("reporter")
    
    nodes = {
        "planner": planner,
        "searcher": searcher,
        "synthesizer": synthesizer,
        "reporter": reporter
    }
    return PocketFlow(nodes, start_node="planner")

# ==========================================================
# Entry Point
# ==========================================================
if __name__ == "__main__":
    flow = create_deep_research_flow()
    config = {"topic": "Impact of microplastics on marine ecosystems"}
    print(f"\n🚀 Starting Deep Research Workflow for: '{config['topic']}'\n")
    result = flow.run(config)
    print(f"\n✅ Workflow Finished. Status: {result['status']}, Iterations: {result['loop_count']}")
    if result.get("status") == "complete":
        print("📄 Report preview (first 300 chars):")
        print(result["report"][:300] + "...")