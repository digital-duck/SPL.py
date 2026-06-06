import os
import json
import re
import requests
from typing import Dict, Any

# ==============================================================================
# SPL Compiler Output: S3-judge-openrouter-qwen.py
# Target: Python — PocketFlow (minimalist ETL-style LLM orchestration)
# ==============================================================================

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = os.environ.get("LLM_MODEL", "qwen/qwen3.6-plus")

def _call_llm(prompt: str) -> str:
    """Minimalist ETL extract node: forwards prompt to OpenRouter/Qwen"""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        # Graceful fallback for zero-config execution per Rule 5
        print("[PocketFlow::MockLLM] OPENROUTER_API_KEY not set. Returning mock payload.")
        if "evaluate" in prompt.lower() or "verdict" in prompt.lower():
            return "VERDICT: pass, Score: 8"
        return "This is a mock high-quality description generated for the provided state."
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}]
    }
    resp = requests.post(OPENROUTER_API_URL, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()

# SPL: CREATE FUNCTION generate_description(state, feedback)
# SPL: RETURNS TEXT AS $$ Generate a high-quality description based on the current state: {state}.
# SPL: If feedback is provided, use it to improve the result: {feedback}
# SPL: Be concise, clear, and do not repeat yourself. $$;
def generate_description(state: str, feedback: str = "") -> str:
    # SPL Prompt Template Rendering
    prompt = (
        f"Generate a high-quality description based on the current state: {state}.\n"
        f"If feedback is provided, use it to improve the result: {feedback}\n"
        "Be concise, clear, and do not repeat yourself."
    )
    # PocketFlow ETL Extract Node
    return _call_llm(prompt)

# SPL: CREATE FUNCTION evaluate_description(description)
# SPL: RETURNS TEXT AS $$ Evaluate the following description for quality: {description}
# SPL: If quality is acceptable (score >= 7), respond with: VERDICT: pass, Score: [score]
# SPL: If quality needs improvement, respond with: VERDICT: fail, Score: [score], Feedback: [specific suggestions] $$;
def evaluate_description(description: str) -> str:
    prompt = (
        f"Evaluate the following description for quality: {description}\n"
        "If quality is acceptable (score >= 7), respond with: VERDICT: pass, Score: [score]\n"
        "If quality needs improvement, respond with: VERDICT: fail, Score: [score], Feedback: [specific suggestions]"
    )
    return _call_llm(prompt)

# SPL: WORKFLOW description_evaluation_loop
# SPL: INPUT @initial_state STRING := "default"
# SPL: OUTPUT @final_result STRING
def S3_judge_openrouter_qwen(initial_state: str = "default") -> Dict[str, Any]:
    # SPL: DO
    # PocketFlow ETL Context Initialization
    context = {
        "shared_state": initial_state,  # SPL: @shared_state := @initial_state;
        "attempts": 0,                  # SPL: @attempts := 0;
        "verdict": "",                  # SPL: @verdict := "";
        "feedback": "",                 # SPL: @feedback := "";
        "status": "retry",              # SPL: @status := "retry";
        "description": ""               # Implicit intermediate buffer
    }

    # SPL: WHILE @attempts <= 2 AND @status = "retry" DO
    while context["attempts"] <= 2 and context["status"] == "retry":
        # SPL: GENERATE generate_description(@shared_state, @feedback) INTO @description;
        context["description"] = generate_description(context["shared_state"], context["feedback"])
        
        # SPL: GENERATE evaluate_description(@description) INTO @verdict;
        context["verdict"] = evaluate_description(context["description"])

        # SPL: EVALUATE @verdict WHEN contains("pass") THEN
        if "pass" in context["verdict"].lower():
            # SPL: @status := "pass";
            context["status"] = "pass"
        # SPL: ELSE
        else:
            # SPL: @attempts := @attempts + 1;
            context["attempts"] += 1
            # SPL: @feedback := @verdict;
            context["feedback"] = context["verdict"]
        # SPL: END;
    # SPL: END;

    # SPL: @final_result := @description;
    final_result = context["description"]
    
    # SPL: RETURN @final_result WITH status = @status;
    return {"final_result": final_result, "status": context["status"]}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--initial-state", required=True, help="Initial state / subject to describe and evaluate")
    args = parser.parse_args()

    result = S3_judge_openrouter_qwen(initial_state=args.initial_state)
    print(json.dumps(result, indent=2))