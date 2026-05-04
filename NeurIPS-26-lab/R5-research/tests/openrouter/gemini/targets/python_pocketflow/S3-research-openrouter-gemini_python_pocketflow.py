#!/usr/bin/env python3
"""
S3-research-openrouter-gemini — compiled from S3-research-openrouter-gemini.spl
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
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


# ---------------------------------------------------------------------------
# SPL: CALL search_web(@searchN) INTO @rawN
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
# SPL CREATE FUNCTION implementations
# ---------------------------------------------------------------------------

def planner_fn(topic: str, feedback: str) -> str:
    prompt = (
        f"You are a research planner. Given the research topic: {topic}\n"
        f"Previous feedback (if any): {feedback}\n\n"
        "Generate exactly 3 specific, diverse search queries to gather comprehensive information.\n"
        "Format your response as:\n"
        "QUERY_1: <first search query>\n"
        "QUERY_2: <second search query>\n"
        "QUERY_3: <third search query>"
    )
    return call_llm(prompt)


def extract_query_fn(queries: str, position: int) -> str:
    prompt = (
        f"From this list of search queries:\n{queries}\n\n"
        f"Extract and return only the search query at position {position}.\n"
        f"For example, if position is 1, return the text after \"QUERY_1: \".\n"
        "Return only the query text with no prefix or extra formatting."
    )
    return call_llm(prompt)


def researcher_fn(query: str) -> str:
    prompt = f"Convert the following query into an optimized search engine string: {query}"
    return call_llm(prompt)


def extractor_fn(raw_results: str) -> str:
    prompt = (
        "Extract key facts and notes from the following search results.\n"
        f"Focus on accuracy and relevance. Don't include fluff.\n"
        f"Raw results: {raw_results}"
    )
    return call_llm(prompt)


def accumulate_notes_fn(existing: str, note1: str, note2: str, note3: str) -> str:
    prompt = (
        "Merge the following research notes into one coherent, organized collection.\n"
        "Remove duplicates and group related facts together.\n\n"
        f"Existing notes:\n{existing}\n\n"
        "New notes from this research iteration:\n"
        f"Batch 1: {note1}\nBatch 2: {note2}\nBatch 3: {note3}\n\n"
        "Return the complete merged notes collection."
    )
    return call_llm(prompt)


def synthesizer_fn(topic: str, notes: str) -> str:
    prompt = (
        f"Evaluate if the following research notes are sufficient to write a "
        f"comprehensive report on \"{topic}\".\n"
        "If more info is needed, respond with \"Need More Info\".\n"
        "If the information is sufficient, respond with \"Sufficient Info\".\n"
        f"Notes: {notes}"
    )
    return call_llm(prompt)


def feedback_generator_fn(topic: str, notes: str) -> str:
    prompt = (
        f"Based on the current notes, what specific information is missing regarding \"{topic}\"?\n"
        "Provide instructions for the planner to refine the next set of queries.\n"
        f"Notes: {notes}"
    )
    return call_llm(prompt)


def finalizer_fn(topic: str, notes: str) -> str:
    prompt = (
        f"Create a final, polished Markdown report about {topic} "
        f"using the provided research notes: {notes}."
    )
    return call_llm(prompt)


# ---------------------------------------------------------------------------
# SPL: WORKFLOW Research_Agent
# ---------------------------------------------------------------------------

def run_research_agent(topic: str, out: str = "report.txt") -> dict:
    """
    SPL: WORKFLOW Research_Agent
           INPUT  @topic TEXT, @out TEXT := "report.txt"
           OUTPUT @report TEXT
    """
    # SPL: @loop_count := 0; @all_notes := ""; @status := "Need More Info"; @feedback := "Initial planning";
    loop_count = 0
    all_notes = ""
    feedback = "Initial planning"

    # SPL: WHILE @loop_count < 2 DO
    while loop_count < 2:
        queries = planner_fn(topic, feedback)

        query1 = extract_query_fn(queries, 1)
        query2 = extract_query_fn(queries, 2)
        query3 = extract_query_fn(queries, 3)

        search1 = researcher_fn(query1)
        search2 = researcher_fn(query2)
        search3 = researcher_fn(query3)

        raw1 = search_web(search1)
        raw2 = search_web(search2)
        raw3 = search_web(search3)

        note1 = extractor_fn(raw1)
        note2 = extractor_fn(raw2)
        note3 = extractor_fn(raw3)

        all_notes = accumulate_notes_fn(all_notes, note1, note2, note3)

        status = synthesizer_fn(topic, all_notes)

        # SPL: EVALUATE @status WHEN contains("Need More Info")
        if "Need More Info" in status:
            feedback = feedback_generator_fn(topic, all_notes)
        else:
            feedback = ""
            if "Sufficient Info" in status:
                break

        loop_count += 1

    # SPL: GENERATE Finalizer(@topic, @all_notes) INTO @report
    report = finalizer_fn(topic, all_notes)

    # SPL: CALL write_file(@out, @report) INTO @write_result
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(report)

    # SPL: RETURN @report WITH status = "complete"
    return {"report": report, "status": "complete", "out": out}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    _topic = sys.argv[1] if len(sys.argv) > 1 else "PocketFlow minimalist LLM framework"
    _out   = sys.argv[2] if len(sys.argv) > 2 else "report.txt"
    result = run_research_agent(_topic, _out)
    print(f"\nStatus : {result['status']}")
    print(f"Report : {result['out']}")
    print(f"\n{result['report'][:500]}...")
