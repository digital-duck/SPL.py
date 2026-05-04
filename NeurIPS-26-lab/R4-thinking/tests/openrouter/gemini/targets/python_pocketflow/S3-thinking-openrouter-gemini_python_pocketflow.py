#!/usr/bin/env python3
"""
S3-thinking-openrouter-gemini — compiled from S3-thinking-openrouter-gemini.spl
Target: Python — PocketFlow (minimalist ETL-style LLM orchestration)
Adapter: openrouter / google/gemini-3-flash-preview
"""
import os
import sys
import requests

_MODEL = "google/gemini-3-flash-preview"
_MAX_ITERATIONS = 10


# ---------------------------------------------------------------------------
# LLM helper — adapter: openrouter
# ---------------------------------------------------------------------------

def call_llm(prompt: str) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": _MODEL, "messages": [{"role": "user", "content": prompt}]},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


# ---------------------------------------------------------------------------
# SPL: CREATE FUNCTION generate_cot_step(history TEXT, plan TEXT)
# ---------------------------------------------------------------------------

def generate_cot_step(history: str, plan: str) -> str:
    prompt = (
        "You are a reasoning engine. Review the current history and plan:\n"
        f"History: {history}\n"
        f"Plan: {plan}\n\n"
        "Generate a response in YAML format:\n"
        "thinking: |\n"
        "  (your current reasoning)\n"
        "plan: |\n"
        "  (updated plan for next steps)\n"
        "next_thought_needed: (true or false)"
    )
    return call_llm(prompt)


# ---------------------------------------------------------------------------
# SPL: CREATE FUNCTION parse_yaml(raw_output TEXT)
# ---------------------------------------------------------------------------

def parse_yaml(raw_output: str) -> str:
    """Extract next_thought_needed boolean from YAML response."""
    lower = raw_output.lower()
    # Look for explicit false signal
    if "next_thought_needed: false" in lower or "next_thought_needed:false" in lower:
        return "false"
    if "next_thought_needed: true" in lower or "next_thought_needed:true" in lower:
        return "true"
    # Default: ask the LLM to extract it
    prompt = (
        f"Extract the 'next_thought_needed' boolean value from this YAML:\n{raw_output}\n"
        "Return only the value: 'true' or 'false'."
    )
    return call_llm(prompt).strip().lower().split()[0]


# ---------------------------------------------------------------------------
# SPL: WORKFLOW chain_of_thought_process
# ---------------------------------------------------------------------------

def run_chain_of_thought(initial_query: str) -> dict:
    """
    SPL: WORKFLOW chain_of_thought_process
           INPUT  @initial_query TEXT
           OUTPUT @final_trace TEXT
    """
    # SPL: @history := @initial_query; @plan := "Initialize reasoning";
    # SPL: @next_thought_needed := "true"; @iteration := 0;
    history = initial_query
    plan = "Initialize reasoning"
    next_thought_needed = "true"
    iteration = 0

    # SPL: WHILE @next_thought_needed = "true" AND @iteration < 10 DO
    while next_thought_needed == "true" and iteration < _MAX_ITERATIONS:
        # SPL: GENERATE generate_cot_step(@history, @plan) INTO @raw_response
        raw_response = generate_cot_step(history, plan)

        # SPL: GENERATE parse_yaml(@raw_response) INTO @next_thought_needed
        next_thought_needed = parse_yaml(raw_response)

        # SPL: @history := @history + "\n---\n" + @raw_response
        history = history + "\n---\n" + raw_response

        # SPL: @iteration := @iteration + 1
        iteration += 1

    # SPL: @final_trace := @history; RETURN @final_trace WITH status = "complete"
    return {"final_trace": history, "status": "complete", "iterations": iteration}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Why is the Fibonacci sequence important?"
    result = run_chain_of_thought(query)
    print(f"\nStatus     : {result['status']}")
    print(f"Iterations : {result['iterations']}")
    print(f"\n--- Final Trace ---\n{result['final_trace']}")
