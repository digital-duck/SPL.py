import os
import re
import yaml
import httpx

# ==============================================================================
# LLM Routing Shim & Helpers
# ==============================================================================
def call_llm(prompt: str, model: str = None) -> str:
    """
    Provider-agnostic LLM call. Reads OPENROUTER_API_KEY or OPENAI_API_KEY,
    and LLM_MODEL from environment. Defaults to OpenAI-compatible endpoints.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    model_name = model or os.environ.get("LLM_MODEL", "gpt-3.5-turbo")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5
    }

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(f"{base_url}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    except Exception:
        # Implicit fallback: returns empty string to trigger safe defaults downstream
        return ""

def parse_yaml_response(text: str) -> dict:
    """Extracts YAML from markdown blocks with implicit fallback on failure."""
    cleaned = re.sub(r"^```(?:yaml)?\n?|```$", "", text.strip(), flags=re.MULTILINE)
    try:
        result = yaml.safe_load(cleaned)
        return result if isinstance(result, dict) else {}
    except yaml.YAMLError:
        return {}

# ==============================================================================
# PocketFlow Nodes
# ==============================================================================
class Node:
    def exec(self, shared: dict) -> str:
        raise NotImplementedError

class Generator(Node):
    """GENERATE: Drafts or revises product description."""
    def exec(self, shared: dict) -> str:
        task = shared.get("task", "Unknown product")
        feedback = shared.get("feedback", "")
        
        prompt = f"""Draft a concise, persuasive product description for: {task}
Constraints: 2-3 sentences max. Output ONLY valid YAML.
Format:
description: <string>
"""
        if feedback:
            prompt += f"\n\nPrevious attempt was rejected. Here is the feedback:\n{feedback}"

        raw = call_llm(prompt)
        data = parse_yaml_response(raw)
        shared["draft"] = data.get("description", raw).strip()
        return "next"

class Judge(Node):
    """EVALUATE: Scores draft, determines verdict, extracts feedback."""
    def exec(self, shared: dict) -> str:
        draft = shared.get("draft", "")
        threshold = int(os.environ.get("SCORE_THRESHOLD", 7))
        max_attempts = int(os.environ.get("MAX_ATTEMPTS", 3))
        
        prompt = f"""Evaluate this product description for clarity and persuasiveness:
"{draft}"

Score on a 1-10 scale. Provide a verdict (PASS or FAIL) and actionable feedback only if FAIL.
Output ONLY valid YAML.
Format:
score: <int>
reasoning: <string>
verdict: <PASS/FAIL>
feedback: <string or null>
"""
        raw = call_llm(prompt)
        data = parse_yaml_response(raw)
        
        shared["score"] = int(data.get("score", 0))
        shared["verdict"] = str(data.get("verdict", "FAIL")).upper()
        shared["feedback"] = data.get("feedback", "")

        # Update attempt counter
        shared["attempts"] = shared.get("attempts", 0) + 1

        # EVALUATE branching logic
        if shared["verdict"] == "PASS" or shared["score"] >= threshold:
            shared["final_description"] = shared["draft"]
            shared["final_score"] = shared["score"]
            return "pass"
            
        if shared["attempts"] >= max_attempts:
            shared["final_description"] = shared["draft"]
            shared["final_score"] = shared["score"]
            return "pass" # Force exit on limit
            
        return "fail" # Loop back for regeneration

# ==============================================================================
# PocketFlow Orchestrator
# ==============================================================================
class PocketFlow:
    """Minimalist ETL-style orchestrator with shared state and conditional routing."""
    def __init__(self, nodes: dict, start_node: str):
        self.nodes = nodes
        self.start_node = start_node
        self.routes = {}
        self.shared = {}

    def route(self, source: str, condition: str, target: str):
        self.routes.setdefault(source, []).append((condition, target))

    def run(self, initial_state: dict) -> dict:
        self.shared = initial_state
        self.shared.setdefault("attempts", 0)
        self.shared.setdefault("feedback", "")
        self.shared.setdefault("draft", "")
        
        current = self.start_node
        max_iter = 20  # Hard safety limit against infinite loops
        
        for _ in range(max_iter):
            node = self.nodes[current]
            status = node.exec(self.shared)
            
            next_node = None
            for cond, target in self.routes.get(current, []):
                if cond == status or cond == "*":
                    next_node = target
                    break
                    
            if next_node is None:
                break  # RETURN / Termination
            current = next_node
            
        return self.shared

# ==============================================================================
# Main Workflow Entry Point
# ==============================================================================
def run_describer_workflow(task_query: str) -> dict:
    generator = Generator()
    judge = Judge()
    
    flow = PocketFlow(
        nodes={"generator": generator, "judge": judge},
        start_node="generator"
    )
    # Wire DAG + Feedback Loop
    flow.route("generator", "next", "judge")
    flow.route("judge", "fail", "generator")
    flow.route("judge", "pass", "*")
    
    result = flow.run({"task": task_query})
    
    # Optional disk persistence
    output_path = "result.yaml"
    with open(output_path, "w") as f:
        yaml.dump({
            "task": result.get("task"),
            "final_score": result.get("final_score"),
            "final_description": result.get("final_description"),
            "attempts_used": result.get("attempts", 0)
        }, f, default_flow_style=False)
        
    return result

if __name__ == "__main__":
    example_task = "An ergonomic bamboo standing desk converter with smooth dual-monitor lifting mechanism."
    print(f"Starting workflow for: {example_task}\n")
    final_state = run_describer_workflow(example_task)
    
    print("\n=== WORKFLOW OUTPUT ===")
    print(f"Final Score : {final_state.get('final_score')}")
    print(f"Attempts    : {final_state.get('attempts')}")
    print(f"Description : {final_state.get('final_description')}")
    print(f"Saved to    : result.yaml")