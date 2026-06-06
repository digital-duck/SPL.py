import os
import json
import yaml
import urllib.request
import sys

# --- LLM Helper ---
def call_llm(prompt: str, model: str = None) -> str:
    """Calls an LLM API using standard library tools. Requires OPENROUTER_API_KEY or OPENAI_API_KEY."""
    model = model or os.environ.get("LLM_MODEL", "anthropic/claude-3-5-sonnet-20240620")
    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("Missing OPENROUTER_API_KEY or OPENAI_API_KEY environment variable.")
        
    base_url = os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
    if "gpt" in model.lower() and not os.environ.get("LLM_BASE_URL"):
        base_url = "https://api.openai.com/v1/chat/completions"
        
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }).encode("utf-8")
    
    req = urllib.request.Request(base_url, data=payload, headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    })
    
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        raise RuntimeError(f"LLM API call failed: {e}")

# --- PocketFlow Minimalist Core ---
class Node:
    """Base node for ETL-style LLM orchestration with prep/exec/post lifecycle."""
    def __init__(self, name=None):
        self.name = name or self.__class__.__name__
        self.default_next = None
        self.named_transitions = {}

    def __rshift__(self, other):
        self.default_next = other
        return other

    def __sub__(self, label):
        class TransitionBuilder:
            def __init__(self, src, lbl):
                self.src, self.lbl = src, lbl
            def __rshift__(self, other):
                self.src.named_transitions[self.lbl] = other
                return other
        return TransitionBuilder(self, label)

    def prep(self, shared):
        return {}
    def exec(self, data):
        return {}
    def post(self, shared, result):
        return None

class Flow:
    """Orchestrates node execution, shared state, and graph transitions."""
    def __init__(self, start_node):
        self.start_node = start_node

    def run(self, shared):
        current = self.start_node
        while current:
            print(f"🔄 Entering node: {current.name}")
            data = current.prep(shared)
            result = current.exec(data)
            label = current.post(shared, result)
            
            # Route based on EVALUATE result or default edge
            if label is None:
                current = current.default_next
            else:
                current = current.named_transitions.get(label)
        return shared

# --- Workflow Prompts ---
INSTRUCTION_BASE = """You are an expert problem solver. You must solve the following problem through iterative, structured self-reflection.
PROBLEM: {problem}
"""

INSTRUCTION_CONTEXT = """
HISTORY OF THOUGHTS:
{thoughts_text}

CURRENT PLAN STATUS:
{last_plan_text}

{is_first_thought}
"""

INSTRUCTION_FORMAT = """
INSTRUCTIONS:
1. Critically audit the last step.
2. Execute the next pending step.
3. Update the hierarchical plan.
4. Decide if further reasoning is required.

OUTPUT STRICT YAML FORMAT:
```yaml
current_thinking: "..."
planning:
  - description: "..."
    status: "Pending|Done|Verification Needed"
    result: "..."
    mark: "..."
    sub_steps: []
next_thought_needed: true|false
```
"""

# --- Chain of Thought Node ---
class ChainOfThoughtNode(Node):
    def __init__(self, name="ChainOfThought"):
        super().__init__(name)

    def prep(self, shared):
        problem = shared.get("problem", "")
        thoughts = shared.get("thoughts", [])
        plan = shared.get("plan", [])
        thought_num = shared.get("current_thought_number", 0)
        
        thoughts_text = "\n".join(thoughts) if thoughts else "None yet."
        last_plan_text = yaml.dump(plan, default_flow_style=False, allow_unicode=True).strip() if plan else "None yet."
        is_first_thought = "This is the first step. Generate an initial three-tier hierarchical plan to approach the problem." if thought_num == 0 else "Resume execution based on prior reasoning steps."
        
        prompt = INSTRUCTION_BASE.format(problem=problem)
        prompt += INSTRUCTION_CONTEXT.format(
            thoughts_text=thoughts_text,
            last_plan_text=last_plan_text,
            is_first_thought=is_first_thought
        )
        prompt += INSTRUCTION_FORMAT
        return {"prompt": prompt}

    def exec(self, data):
        print("📡 Calling LLM...")
        response = call_llm(data["prompt"])
        return {"raw_response": response}

    def post(self, shared, result):
        raw = result.get("raw_response", "")
        # Strip markdown code blocks if present
        if "```yaml" in raw:
            raw = raw.split("```yaml")[1].split("```")[0]
        elif "```" in raw:
            parts = raw.split("```")
            raw = parts[1].strip() if len(parts) > 1 else raw.strip()
            
        # EXCEPTION HANDLER: Schema validation & parsing safety
        try:
            thought_data = yaml.safe_load(raw)
            assert isinstance(thought_data, dict), "Output must be a dictionary"
            assert "current_thinking" in thought_data, "Missing 'current_thinking'"
            assert "planning" in thought_data, "Missing 'planning'"
            assert "next_thought_needed" in thought_data, "Missing 'next_thought_needed'"
        except Exception as e:
            print(f"⚠️  EXCEPTION HANDLER: YAML Parse/Schema Error: {e}")
            print("Raw output snippet:", raw[:200])
            shared["solution"] = "Failed to generate valid reasoning step due to LLM format deviation."
            shared["status"] = "error"
            return "end"

        # Update shared state
        thought_num = shared.get("current_thought_number", 0) + 1
        shared["current_thought_number"] = thought_num
        
        new_thinking = thought_data["current_thinking"]
        shared["thoughts"].append(f"## Thought {thought_num}\n{new_thinking}")
        shared["plan"] = thought_data["planning"]
        
        # Stream progress to stdout
        print(f"\n[Step {thought_num}] Executed: {new_thinking[:100]}...")
        for item in shared["plan"]:
            status = item.get("status", "Unknown")
            desc = item.get("description", "Task")
            res = item.get("result", "")
            print(f"  - [{status}] {desc} | Result: {res[:50]}")

        # EVALUATE: Inspect continuation flag
        if not thought_data.get("next_thought_needed", True):
            print("\n✅ EVALUATE: next_thought_needed is False. Terminating loop.")
            shared["solution"] = new_thinking
            shared["status"] = "solved"
            shared["iterations"] = thought_num
            
            # Side-effect: Optional disk persistence
            output_path = shared.get("output_path")
            if output_path:
                with open(output_path, "w", encoding="utf-8") as f:
                    yaml.dump(shared, f, default_flow_style=False, allow_unicode=True)
                print(f"💾 Solution persisted to {output_path}")
            return "end"
            
        return "continue"

# --- Workflow Factory ---
def create_chain_of_thought_flow():
    cot_node = ChainOfThoughtNode()
    # Self-loop for continue condition, implicit termination on "end"
    cot_node - "continue" >> cot_node
    return Flow(start_node=cot_node)

# --- Entry Point ---
if __name__ == "__main__":
    problem_text = """
    You have a 3-gallon jug and a 5-gallon jug. You need to measure exactly 4 gallons of water.
    You have an unlimited water supply. How do you do it? Provide step-by-step instructions.
    """
    
    shared_state = {
        "problem": problem_text.strip(),
        "thoughts": [],
        "plan": [],
        "current_thought_number": 0,
        "solution": None,
        "status": "pending",
        "output_path": "cot_solution.yaml"
    }
    
    print("🚀 Initializing Chain-of-Thought Workflow...")
    flow = create_chain_of_thought_flow()
    final_state = flow.run(shared_state)
    
    print("\n" + "="*50)
    print("🏁 WORKFLOW COMPLETE")
    print(f"Status: {final_state.get('status')}")
    print(f"Iterations: {final_state.get('iterations')}")
    print(f"Final Solution:\n{final_state.get('solution')}")
    print("="*50)