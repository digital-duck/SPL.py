#!/usr/bin/env python3
"""
S3-agent-openrouter-gemini — compiled from S3-agent-openrouter-gemini.spl
Target: Python — PocketFlow (minimalist ETL-style LLM orchestration)
Adapter: openrouter / google/gemini-3-flash-preview
"""
import os
import sys
import requests
from duckduckgo_search import DDGS

_MODEL = "google/gemini-3-flash-preview"


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
# SPL: CALL search_web(@user_query) INTO @search_results
# ---------------------------------------------------------------------------

def search_web(query: str) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        if not results:
            return f"No results found for: {query}"
        return "\n".join(f"- {r['title']}: {r['body']}" for r in results)
    except Exception as exc:
        return f"Search error: {exc}"


# ---------------------------------------------------------------------------
# SPL: CREATE FUNCTION DecideAction(user_query TEXT, context TEXT)
# ---------------------------------------------------------------------------

def decide_action(user_query: str, context: str) -> str:
    prompt = (
        f"Given the question: {user_query}\n"
        f"Current research context: {context}\n\n"
        "Decide if you need to perform a web search to gather more information, "
        "or if you have enough information to answer.\n"
        "Respond with exactly one word: 'search' or 'answer'."
    )
    return call_llm(prompt)


# ---------------------------------------------------------------------------
# SPL: CREATE FUNCTION AnswerQuestion(user_query TEXT, context TEXT)
# ---------------------------------------------------------------------------

def answer_question(user_query: str, context: str) -> str:
    prompt = (
        f"Based on the question: {user_query}\n"
        f"And the gathered context: {context}\n\n"
        "Synthesize a final comprehensive response to the question."
    )
    return call_llm(prompt)


# ---------------------------------------------------------------------------
# SPL: WORKFLOW ResearchAssistant
# ---------------------------------------------------------------------------

def run_research_assistant(user_query: str) -> dict:
    """
    SPL: WORKFLOW ResearchAssistant
           INPUT  @user_query TEXT
           OUTPUT @final_response TEXT
    """
    # SPL: @context := "No information gathered yet"; @action := "search"; @iteration := 0;
    context = "No information gathered yet"
    action = "search"
    iteration = 0

    # SPL: WHILE @action = "search" AND @iteration < 5 DO
    while "search" in action.lower() and iteration < 5:
        # SPL: GENERATE DecideAction(@user_query, @context) INTO @action
        action = decide_action(user_query, context)

        # SPL: EVALUATE @action WHEN contains("search") THEN
        if "search" in action.lower():
            # SPL: CALL search_web(@user_query) INTO @search_results
            search_results = search_web(user_query)
            # SPL: @context := @context + "\nNew Findings: " + @search_results
            context += f"\nNew Findings: {search_results}"
            # SPL: @iteration := @iteration + 1
            iteration += 1
        else:
            # SPL: ELSE @action := "done"
            action = "done"

    # SPL: GENERATE AnswerQuestion(@user_query, @context) INTO @final_response
    final_response = answer_question(user_query, context)

    # SPL: RETURN @final_response WITH status = "complete"
    return {"final_response": final_response, "status": "complete", "iterations": iteration}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is PocketFlow and how do I install it?"
    result = run_research_assistant(query)
    print(f"\nStatus     : {result['status']}")
    print(f"Iterations : {result['iterations']}")
    print(f"\nAnswer:\n{result['final_response']}")
