import os
import re
import yaml
import requests
from typing import Dict, Any

# --- LLM HELPER ---
def call_llm(prompt: str, model: str = None) -> str:
    """
    Calls an LLM using OpenRouter or OpenAI-compatible API.
    Reads config from environment variables.
    """
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("API Key not found. Please set OPENROUTER_API_KEY or OPENAI_API_KEY.")
    
    model = model or os.getenv("LLM_MODEL", "meta-llama/llama-3-70b-instruct")
    base_url = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    try:
        response = requests.post(base_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error calling LLM: {str(e)}"

# --- POCKETFLOW CORE (Minimalist Implementation) ---
class Node:
    def __init__(self):
        self.next_node = None

    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        return shared

    def exec(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        return inputs

    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        return "default"

class Flow:
    def __init__(self, start_node: Node):
        self.nodes = {}
        self.start_node = start_node
        self.transitions = {}

    def add_transition(self, from_node: Node, status: str, to_node: Node):
        from_name = from_node.__class__.__name__
        if from_name not in self.transitions:
            self.transitions[from_name] = {}
        self.transitions[from_name][status] = to_node

    def run(self, initial_state: Dict[str, Any]):
        shared = initial_state
        current_node = self.start_node
        
        while current_node:
            print(f"[Node]: {current_node.__class__.__name__}")
            prep_res = current_node.prep(shared)
            exec_res = current_node.exec(prep_res)
            status = current_node.post(shared, prep_res, exec_res)
            
            node_name = current_node.__class__.__name__
            if node_name in self.transitions and status in self.transitions[node_name]:
                current_node = self.transitions[node_name][status]
            else:
                current_node = None
        return shared

# --- WORKFLOW NODES ---

def extract_yaml(text: str) -> Dict[str, Any]:
    """Helper to extract YAML content from LLM block."""
    match = re.search(r"```yaml\n(.*?)\n```", text, re.DOTALL)
    if match:
        return yaml.safe_load(match.group(1))
    # Fallback to simple search if block markers are missing
    try: return yaml.safe_load(text)
    except: return {}

class Generator(Node):
    def exec(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        task = inputs.get("task")
        feedback = inputs.get("feedback", "None. This is the first draft.")
        attempts = inputs.get("attempts", 0)
        
        prompt = f"""
        Task: {task}
        Previous Feedback: {feedback}
        
        Create a compelling product marketing description.
        Return your response strictly in the following YAML format:
        
        ```yaml
        description: "The marketing text here"
        ```
        """
        response = call_llm(prompt)
        data = extract_yaml(response)
        return {"draft": data.get("description", "Error generating draft"), "attempts": attempts + 1}

    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        shared["draft"] = exec_res["draft"]
        shared["attempts"] = exec_res["attempts"]
        return "to_judge"

class Judge(Node):
    def exec(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        draft = inputs.get("draft")
        prompt = f"""
        Evaluate the following product marketing description for clarity and persuasiveness.
        Score it from 1 to 10.
        
        Description: {draft}
        
        Return your response strictly in the following YAML format:
        ```yaml
        score: <integer>
        reasoning: "Brief explanation"
        verdict: "PASS" or "FAIL" (PASS if score >= 7)
        feedback: "Specific suggestions for improvement"
        ```
        """
        response = call_llm(prompt)
        return extract_yaml(response)

    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        shared["score"] = exec_res.get("score", 0)
        shared["feedback"] = exec_res.get("feedback", "No feedback provided.")
        shared["reasoning"] = exec_res.get("reasoning", "")
        
        verdict = str(exec_res.get("verdict", "FAIL")).upper()
        attempts = shared.get("attempts", 0)
        
        print(f"  -> Attempt {attempts} Score: {shared['score']} | Verdict: {verdict}")

        if verdict == "PASS" or attempts >= 3:
            return "finish"
        else:
            return "retry"

# --- WORKFLOW ORCHESTRATION ---

def create_judge_flow():
    generator = Generator()
    judge = Judge()
    
    flow = Flow(start_node=generator)
    
    # Define transitions
    flow.add_transition(generator, "to_judge", judge)
    flow.add_transition(judge, "retry", generator)
    flow.add_transition(judge, "finish", None) # End flow
    
    return flow

if __name__ == "__main__":
    # Example Input
    input_task = {
        "task": "Write a 2-sentence marketing description for a 'Smart Self-Cleaning Water Bottle' targeted at busy hikers.",
        "attempts": 0,
        "feedback": ""
    }
    
    marketing_flow = create_judge_flow()
    final_state = marketing_flow.run(input_task)
    
    print("\n" + "="*50)
    print("FINAL OUTPUT")
    print("="*50)
    print(f"Final Score: {final_state.get('score')}/10")
    print(f"Attempts: {final_state.get('attempts')}")
    print(f"Description: {final_state.get('draft')}")
    print(f"Reasoning: {final_state.get('reasoning')}")
    print("="*50)