import os
import sys
import yaml
import argparse
import logging
import requests
from duckduckgo_search import DDGS
from pocketflow import Node, Flow

# --- Configuration & Logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger(__name__)

# --- LLM & Tool Helpers ---

def call_llm(prompt: str, model: str = "google/gemini-3-flash-preview") -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY environment variable is required.")

    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()

def search_web(query: str) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        if not results:
            return "No relevant search results found."
        return "\n".join(f"- {r['title']}: {r['body']}" for r in results)
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return f"Search tool error: {e}"

def parse_yaml(raw: str) -> dict:
    """Parse YAML with block-scalar (`|`) fallback retry for malformed LLM output."""
    try:
        res = yaml.safe_load(raw)
        return res if isinstance(res, dict) else {}
    except yaml.YAMLError:
        pass

    # Exception handler fallback: force block-scalar on known keys
    known_keys = ["action", "search_query", "answer"]
    fixed_lines = []
    for line in raw.split("\n"):
        stripped = line.strip()
        matched = False
        for k in known_keys:
            if stripped.startswith(f"{k}:"):
                val = stripped[len(k) + 1:].strip()
                if val and not val.startswith("|") and not val.startswith("'") and not val.startswith('"'):
                    fixed_lines.append(f"{k}: |")
                    fixed_lines.append(f"  {val}")
                else:
                    fixed_lines.append(line)
                matched = True
                break
        if not matched:
            fixed_lines.append(line)

    fixed_raw = "\n".join(fixed_lines)
    try:
        res = yaml.safe_load(fixed_raw)
        return res if isinstance(res, dict) else {}
    except yaml.YAMLError:
        logger.warning("YAML parse failed even after fallback. Defaulting to answer.")
        return {"action": "answer"}

# --- PocketFlow Nodes ---

class DecideNode(Node):
    def prep(self, shared: dict):
        return shared["question"], shared.get("context", ""), shared.get("model", "google/gemini-3-flash-preview")

    def exec(self, args):
        question, context, model = args
        prompt = f"""You are a research agent. Evaluate the accumulated context to decide the next step.
Question: {question}
Accumulated Context:
{context}

Output ONLY valid YAML with exactly these keys:
- 'action': either "search" or "answer"
- 'search_query': (required if action is "search") a concise search query
- 'answer': (optional, if action is "answer") a brief placeholder

Example:
action: search
search_query: "latest advancements in solid-state batteries 2024"
"""
        raw = call_llm(prompt, model=model)
        return parse_yaml(raw)

    def post(self, shared: dict, prep_res, exec_res):
        shared["decision"] = exec_res
        shared["iteration"] = shared.get("iteration", 0) + 1
        
        # Safety guard against infinite loops
        max_iter = 5
        if shared["iteration"] > max_iter:
            logger.info(f"Max iterations ({max_iter}) reached. Forcing answer synthesis.")
            return "answer"
            
        action = exec_res.get("action", "answer")
        logger.info(f"DecideNode -> Action: {action} | Query: {exec_res.get('search_query', 'N/A')}")
        return action

class SearchNode(Node):
    def prep(self, shared: dict):
        return shared["decision"].get("search_query", shared["question"])

    def exec(self, query: str):
        logger.info(f"Searching web for: '{query}'")
        return search_web(query)

    def post(self, shared: dict, prep_res, exec_res):
        current = shared.get("context", "")
        if current:
            shared["context"] = f"{current}\n---\n{exec_res}"
        else:
            shared["context"] = exec_res
        logger.info(f"SearchNode -> Context updated ({len(exec_res)} chars). Looping back to Decide.")
        return "default"

class AnswerNode(Node):
    def prep(self, shared: dict):
        return shared["question"], shared.get("context", ""), shared.get("model", "google/gemini-3-flash-preview")

    def exec(self, args):
        question, context, model = args
        prompt = f"""Synthesize a comprehensive, well-structured final answer based on the research context.
Question: {question}
Research Context:
{context}

Provide a detailed answer. If information is missing, state what is known and note gaps.
Answer:
"""
        return call_llm(prompt, model=model)

    def post(self, shared: dict, prep_res, exec_res):
        shared["answer"] = exec_res
        shared["status"] = "done"
        logger.info("AnswerNode -> Synthesis complete. Workflow terminating.")
        return "done"

# --- Main Execution ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Iterative Research Agent using PocketFlow")
    parser.add_argument("question", help="The research question to answer")
    parser.add_argument("--model", default="google/gemini-3-flash-preview", help="OpenRouter model ID")
    args = parser.parse_args()

    shared = {
        "question": args.question,
        "context": "",
        "model": args.model,
        "iteration": 0,
    }

    # Instantiate nodes
    decide = DecideNode()
    search = SearchNode()
    answer = AnswerNode()

    # Wire the graph (WHILE loop pattern)
    # Conditional branch from Decide
    decide - "search" >> search
    decide - "answer" >> answer
    # Unconditional back-edge from Search to Decide (implements WHILE loop)
    search >> decide

    flow = Flow(start=decide)
    logger.info(f"🔍 Starting research for: '{args.question}' using model '{args.model}'...")

    try:
        flow.run(shared)
    except Exception as e:
        logger.error(f"❌ Workflow failed: {e}")
        sys.exit(1)

    # Output result
    print("\n" + "="*60)
    print("✅ RESEARCH COMPLETE")
    print(f"📊 Status: {shared.get('status')}")
    print(f"📝 Answer:\n{shared.get('answer', 'No answer generated.')}")
    print("="*60)