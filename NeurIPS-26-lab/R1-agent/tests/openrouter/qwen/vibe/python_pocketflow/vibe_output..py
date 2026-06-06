import os
import re
import sys
import json
import logging
from typing import Any, Dict, Optional
import yaml
from openai import OpenAI
from duckduckgo_search import DDGS

# Attempt to import PocketFlow. Fallback to minimal inline implementation if not installed.
try:
    from pocketflow import Node, Flow
except ImportError:
    import warnings
    warnings.warn("pocketflow not found. Using minimal inline compatibility layer.")
    class Node:
        def exec(self, shared: Dict[str, Any]) -> Any:
            raise NotImplementedError
        def post(self, shared: Dict[str, Any], prep_res: Any, exec_res: Any) -> Optional[str]:
            raise NotImplementedError
    class Flow:
        def __init__(self, nodes: Dict[str, Node], start: str):
            self.nodes = nodes
            self.start = start
        def run(self, shared: Dict[str, Any]):
            current = self.start
            while current and current != "done":
                if current not in self.nodes:
                    raise ValueError(f"Node '{current}' not found in flow.")
                node = self.nodes[current]
                exec_res = node.exec(shared)
                current = node.post(shared, None, exec_res)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def call_llm(prompt: str, model: str = None) -> str:
    model = model or os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("Missing API key. Set OPENROUTER_API_KEY or OPENAI_API_KEY environment variable.")
    
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    return response.choices[0].message.content.strip()

def search_web_duckduckgo(query: str, max_results: int = 3) -> str:
    logger.info(f"Executing web search for: '{query}'")
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(f"Title: {r['title']}\nSnippet: {r['body']}\nURL: {r['href']}")
        return "\n---\n".join(results) if results else "No search results returned."
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return f"Search execution error: {str(e)}"

def parse_yaml_safely(text: str) -> Dict[str, Any]:
    """EXCEPTION handler: attempts parsing, applies heuristic repairs, retries, then falls back to regex."""
    def repair(text):
        text = text.strip()
        text = re.sub(r'^```(?:yaml|yml)?\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\s*```\s*$', '', text, flags=re.MULTILINE)
        # Attempt to fix missing quotes on unquoted strings
        text = re.sub(r'(\w+):\s*([^:\n"\'|{}][^\n]*)', r'\1: "\2"', text)
        return text

    for attempt in range(2):
        try:
            data = yaml.safe_load(text)
            if isinstance(data, dict) and "action" in data:
                return data
        except yaml.YAMLError:
            if attempt == 0:
                text = repair(text)
                logger.warning("YAML parse failed. Applying heuristic repair and retrying.")
                continue
            else:
                logger.warning("YAML parse failed after retry. Falling back to regex extraction.")
    
    # Final regex fallback
    data = {}
    for key in ["action", "search_query", "thinking", "reason", "answer"]:
        match = re.search(rf"{key}:\s*(?:\|\s*\n)?((?:[^\n]+\n?)+)", text, re.IGNORECASE | re.MULTILINE)
        if match:
            data[key] = match.group(1).strip()
    return data if "action" in data else {"action": "search", "search_query": ""}

class DecideAction(Node):
    def exec(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        question = shared.get("question", "")
        context = shared.get("context", "")
        prompt = f"""You are an autonomous research orchestrator. Evaluate the current research gap and decide whether to search for more information or synthesize a final answer.
Output STRICTLY valid YAML. Use pipe block scalars (|) for multi-line strings to prevent syntax breaks.
Required Structure:
action: search | answer
thinking: |
  Your step-by-step evaluation of the research gap.
reason: |
  Justification for the chosen action.
search_query: |
  (Only if action=search) Precise, optimized web search query.
answer: |
  (Only if action=answer) Draft or final response.

Question: {question}
Accumulated Context: {context or "None yet."}
"""
        raw = call_llm(prompt)
        return parse_yaml_safely(raw)

    def post(self, shared: Dict[str, Any], prep_res: Any, exec_res: Dict[str, Any]) -> str:
        try:
            action = exec_res.get("action", "").lower().strip()
        except AttributeError:
            action = "search"

        if action == "search":
            shared["search_query"] = exec_res.get("search_query", shared.get("question", ""))
            logger.info(f"Routing: SEARCH -> {shared['search_query']}")
            return "search_web"
        elif action == "answer":
            logger.info("Routing: ANSWER")
            return "answer_question"
        else:
            logger.warning(f"Unknown action '{action}'. Defaulting to search.")
            shared["search_query"] = shared.get("question", "")
            return "search_web"

class SearchWeb(Node):
    def exec(self, shared: Dict[str, Any]) -> str:
        query = shared.get("search_query", "")
        return search_web_duckduckgo(query)

    def post(self, shared: Dict[str, Any], prep_res: Any, exec_res: str) -> str:
        prev = shared.get("context", "")
        new_block = f"\n### Research for '{shared.get('search_query', 'unknown')}':\n{exec_res}"
        shared["context"] = prev + new_block
        logger.info("Accumulated context updated. Looping back to decision phase.")
        return "decide_action"

class AnswerQuestion(Node):
    def exec(self, shared: Dict[str, Any]) -> str:
        question = shared.get("question", "")
        context = shared.get("context", "")
        prompt = f"""You are an expert researcher. Synthesize a comprehensive, authoritative answer to the user's question based strictly on the accumulated research findings.
Question: {question}
Research Context:
{context}

Provide a direct, well-structured response. Do not include meta-commentary, process descriptions, or wrapper tags.
"""
        logger.info("Generating final synthesis.")
        return call_llm(prompt)

    def post(self, shared: Dict[str, Any], prep_res: Any, exec_res: str) -> str:
        shared["answer"] = exec_res
        logger.info("Workflow complete. Returning status: done")
        print("\n" + "="*60)
        print("✅ RESEARCH COMPLETE")
        print("="*60)
        print(exec_res)
        print("="*60)
        return "done"

def run_research_workflow(question: str, max_iterations: int = 5) -> str:
    shared = {
        "question": question,
        "context": "",
        "search_query": "",
        "answer": ""
    }
    
    # Node instantiation
    nodes = {
        "decide_action": DecideAction(),
        "search_web": SearchWeb(),
        "answer_question": AnswerQuestion()
    }
    
    flow = Flow(nodes=nodes, start="decide_action")
    flow.run(shared)
    
    return shared.get("answer", "Workflow finished without generating an answer.")

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What are the latest breakthroughs in solid-state battery technology as of 2024?"
    print(f"🚀 Starting ReAct research agent for: '{query}'\n")
    
    try:
        final_answer = run_research_workflow(query)
        with open("research_output.txt", "w", encoding="utf-8") as f:
            f.write(f"Question: {query}\n\nFinal Answer:\n{final_answer}")
        print(f"\n📄 Output persisted to research_output.txt")
    except Exception as e:
        logger.critical(f"Fatal workflow error: {e}", exc_info=True)
        sys.exit(1)