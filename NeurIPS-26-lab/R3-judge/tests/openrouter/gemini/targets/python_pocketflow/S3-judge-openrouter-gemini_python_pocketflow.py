#!/usr/bin/env python3
"""
S3-judge-openrouter-gemini — compiled from S3-judge-openrouter-gemini.spl
Target: Python — PocketFlow (minimalist ETL-style LLM orchestration)
Adapter: openrouter / google/gemini-3-flash-preview
"""
import os
import sys
import requests

_MODEL = "google/gemini-3-flash-preview"
_MAX_ATTEMPTS = 3


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
# SPL: CREATE FUNCTION draft_content(topic TEXT)
# ---------------------------------------------------------------------------

def draft_content(topic: str, feedback: str = "") -> str:
    prompt = (
        f"Draft a high-quality, detailed article about: {topic}\n"
        f"Focus on clarity and technical accuracy.\n"
        + (f"Previous feedback to address: {feedback}" if feedback else "")
    )
    return call_llm(prompt)


# ---------------------------------------------------------------------------
# SPL: CREATE FUNCTION evaluate_content(topic TEXT, content TEXT)
# ---------------------------------------------------------------------------

def evaluate_content(topic: str, content: str) -> str:
    prompt = (
        f"You are a strict quality judge evaluating content about: {topic}\n\n"
        f"Content to evaluate:\n{content}\n\n"
        "If it meets quality standards (accurate, clear, comprehensive), "
        "respond with: PASS\n"
        "If it is insufficient, respond with: FAIL\n"
        "Then on a new line provide brief feedback on what to improve."
    )
    return call_llm(prompt)


# ---------------------------------------------------------------------------
# SPL: WORKFLOW content_refinement_process
# ---------------------------------------------------------------------------

def run_content_refinement(topic: str) -> dict:
    """
    SPL: WORKFLOW content_refinement_process
           INPUT  @topic TEXT
           OUTPUT @final_result TEXT
    """
    # SPL: @attempts := 0; @verdict := "FAIL"; @content := ""; @feedback := "Initial draft"
    attempts = 0
    verdict = "FAIL"
    content = ""
    feedback = "Initial draft"

    # SPL: WHILE @verdict = "FAIL" AND @attempts < 3 DO
    while "FAIL" in verdict and attempts < _MAX_ATTEMPTS:
        attempts += 1

        # SPL: GENERATE draft_content(@topic, @feedback) INTO @content
        content = draft_content(topic, feedback if attempts > 1 else "")

        # SPL: GENERATE evaluate_content(@topic, @content) INTO @verdict
        verdict = evaluate_content(topic, content)

        # SPL: EVALUATE @verdict WHEN contains("FAIL")
        if "FAIL" in verdict:
            feedback = verdict  # full judge response used as feedback
        else:
            feedback = "Content passed evaluation."

    # SPL: @final_result := @content; RETURN WITH status = "complete"
    return {
        "final_result": content,
        "status": "complete" if "PASS" in verdict else "max_attempts",
        "attempts": attempts,
        "verdict": verdict,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "explain quantum entanglement for a high-school student"
    result = run_content_refinement(topic)
    print(f"\nStatus   : {result['status']}")
    print(f"Attempts : {result['attempts']}")
    print(f"\n--- Final Description ---\n{result['final_result']}")
    print(f"\n--- Final Score ---\n{result['verdict']}")
