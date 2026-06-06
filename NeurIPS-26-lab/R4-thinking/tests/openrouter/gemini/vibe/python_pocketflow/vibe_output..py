import os
import yaml
import json
import requests
from typing import Dict, Any, List

# --- LLM UTILITY ---
def call_llm(prompt: str, model: str = None) -> str:
    """
    Calls the LLM via OpenRouter/OpenAI compatible API.
    """
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("API Key not found. Please set OPENROUTER_API_KEY or OPENAI_API_KEY.")
    
    model = model or os.getenv("LLM_MODEL", "meta-llama/llama-3-70b-instruct")
    base_url = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    response = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

# --- POCKETFLOW CORE ---
class Node:
    def __init__(self):
        self.transitions = {}

    def __sub__(self, action):
        return ConnectionBuilder(self, action)

    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        return shared

    def exec(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        return inputs

    def post(self, shared: Dict[str, Any], outputs: Dict[str, Any]) -> str:
        return "default"

class ConnectionBuilder:
    def __init__(self, node, action):
        self.node = node
        self.action = action

    def __gt__(self, next_node):
        self.node.transitions[self.action] = next_node
        return next_node

class Flow:
    def __init__(self, start_node: Node):
        self.start_node = start_node

    def run(self, shared: Dict[str, Any]):
        current_node = self.start_node
        while current_node:
            inputs = current_node.prep(shared)
            outputs = current_node.exec(inputs)
            shared.update(outputs)
            action = current_node.post(shared, outputs)
            current_node = current_node.transitions.get(action)
        return shared

# --- WORKFLOW IMPLEMENTATION ---

class ChainOfThoughtNode(Node):
    """
    The central reasoning engine. Manages state, calls LLM, and parses YAML.
    """
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        shared["current_thought_number"] = shared.get("current_thought_number", 0) + 1
        return shared

    def exec(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._build_prompt(inputs)
        raw_response = call_llm(prompt)
        
        # Extract YAML from code blocks
        yaml_content = raw_response
        if "```yaml" in raw_response:
            yaml_content = raw_response.split("```yaml")[1].split("```")[0].strip()
        elif "```" in raw_response:
            yaml_content = raw_response.split("```")[1].split("```")[0].strip()

        try:
            parsed = yaml.safe_load(yaml_content)
        except Exception as e:
            # Fallback for parsing errors
            parsed = {
                "current_thinking": f"Error parsing LLM response: {str(e)}. Original: {raw_response}",
                "planning": inputs.get("planning", []),
                "next_thought_needed": False
            }

        # Update History
        thoughts = inputs.get("thoughts", [])
        thoughts.append({
            "step": inputs["current_thought_number"],
            "thinking": parsed.get("current_thinking", ""),
            "evaluation": parsed.get("evaluation", "N/A")
        })

        return {
            "thoughts": thoughts,
            "planning": parsed.get("planning", []),
            "next_thought_needed": parsed.get("next_thought_needed", False),
            "final_answer": parsed.get("current_thinking") if not parsed.get("next_thought_needed") else None
        }

    def post(self, shared: Dict[str, Any], outputs: Dict[str, Any]) -> str:
        if outputs.get("next_thought_needed"):
            return "continue"
        return "done"

    def _build_prompt(self, state: Dict[str, Any]) -> str:
        history_str = json.dumps(state.get("thoughts", []), indent=2)
        plan_str = json.dumps(state.get("planning", []), indent=2)
        
        return f"""
You are a structured reasoning engine. Solve the following problem using a step-by-step Chain-of-Thought process.

PROBLEM:
{state['problem']}

HISTORY OF THOUGHTS:
{history_str}

CURRENT PLAN:
{plan_str}

TASK:
1. Evaluate the previous step (if any). Start with "Evaluation of Thought {state['current_thought_number']-1}: [Correct/Minor Issues/Major Error]".
2. Execute the next logical step from the plan.
3. Update the plan (mark items done, add sub-tasks, or correct course).
4. Decide if further steps are needed. If you have reached a final conclusion, set next_thought_needed to false.

OUTPUT FORMAT:
Return ONLY a valid YAML block:
```yaml
evaluation: "Brief assessment of previous thought"
current_thinking: "Detailed reasoning for the current step"
planning:
  - task: "Task description"
    status: "Pending/Done"
next_thought_needed: true/false
```
"""

def create_chain_of_thought_flow():
    cot_node = ChainOfThoughtNode()
    
    # Loop wiring: If post returns "continue", loop back to self.
    cot_node - "continue" >> cot_node
    
    return Flow(cot_node)

# --- ENTRY POINT ---
if __name__ == "__main__":
    # Example setup
    initial_state = {
        "problem": "A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. How much does the ball cost? Think carefully, verify your math, and confirm the total sum.",
        "thoughts": [],
        "planning": [
            {"task": "Identify variables and set up equations", "status": "Pending"},
            {"task": "Solve for the ball price", "status": "Pending"},
            {"task": "Verify the result with the total sum constraint", "status": "Pending"},
            {"task": "Conclusion", "status": "Pending"}
        ]
    }

    flow = create_chain_of_thought_flow()
    final_state = flow.run(initial_state)

    print("\n--- FINAL REASONING TRACE ---")
    for t in final_state["thoughts"]:
        print(f"\n[Step {t['step']}]")
        print(f"Eval: {t['evaluation']}")
        print(f"Thinking: {t['thinking']}")
    
    print("\n--- RESULT ---")
    print(final_state.get("final_answer"))