#!/usr/bin/env python3
"""
S3-research-claude_cli-sonnet — PocketFlow implementation
Compiled from: S3-research-claude_cli-sonnet.spl
Target:        Python — PocketFlow (minimalist ETL-style LLM orchestration)
"""

import subprocess
import concurrent.futures
import sys
from pocketflow import Node, Flow


# ---------------------------------------------------------------------------
# LLM helper — adapter: claude_cli, model: sonnet
# ---------------------------------------------------------------------------

def call_llm(prompt: str) -> str:
    result = subprocess.run(
        ["claude", "-p", prompt, "--model", "claude-sonnet-4-6"],
        capture_output=True, text=True, timeout=180,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI error: {result.stderr.strip()}")
    return result.stdout.strip()


# SPL: CALL search_web(@queryN) — tool call (not GENERATE)
# Replace body with SerpAPI / Brave Search / Tavily for production use.
def search_web(query: str) -> str:
    result = subprocess.run(
        ["claude", "-p",
         f"Search the web for: {query}\n"
         "Return a detailed summary of the most relevant findings.",
         "--model", "claude-sonnet-4-6"],
        capture_output=True, text=True, timeout=180,
    )
    if result.returncode != 0:
        raise RuntimeError(f"search_web error: {result.stderr.strip()}")
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# Prompt templates — SPL CREATE FUNCTION definitions
# ---------------------------------------------------------------------------

# SPL: CREATE FUNCTION planner(topic, feedback)
PLANNER_PROMPT = """\
You are a research planner. Given the research topic: {topic}
And previous iteration feedback (if any): {feedback}

Generate exactly 3 specific, diverse search queries to gather comprehensive information.
Format your response as:
QUERY_1: <first search query>
QUERY_2: <second search query>
QUERY_3: <third search query>"""

# SPL: CREATE FUNCTION extract_query(queries, position)
EXTRACT_QUERY_PROMPT = """\
From this list of search queries:
{queries}

Extract and return only the search query at position {position}.
For example, if position is 1, return the text after "QUERY_1: ".
Return only the query text with no prefix or extra formatting."""

# SPL: CREATE FUNCTION extract_facts(query, result)
EXTRACT_FACTS_PROMPT = """\
Given the search query: {query}
And the search result content: {result}

Extract and summarize the key facts and relevant information as a concise bullet-point list.
Focus on information directly relevant to the query."""

# SPL: CREATE FUNCTION accumulate_notes(existing_notes, note1, note2, note3)
ACCUMULATE_NOTES_PROMPT = """\
Merge the following research notes into one coherent, organized collection.
Remove duplicates and group related facts together.

Existing notes:
{existing_notes}

New notes from this research iteration:
Batch 1: {note1}
Batch 2: {note2}
Batch 3: {note3}

Return the complete merged notes collection."""

# SPL: CREATE FUNCTION synthesizer(topic, notes, loop_count)
SYNTHESIZER_PROMPT = """\
You are a research synthesizer. Evaluate the research gathered so far.

Topic: {topic}
Research iteration: {loop_count}
Accumulated notes: {notes}

Decide whether to continue researching or finalize the report.

If the notes provide sufficient coverage, respond with:
DECISION: finalize
REPORT: <write the complete, well-structured research report here>

If important information is still missing, respond with:
DECISION: research
FEEDBACK: <describe specifically what information is still needed>

Begin your response with either "DECISION: finalize" or "DECISION: research"."""

# SPL: CREATE FUNCTION extract_report(decision)
EXTRACT_REPORT_PROMPT = """\
From the following synthesizer output:
{decision}

Extract and return only the content that appears after "REPORT: ".
Return the full report text with no additional prefix."""

# SPL: CREATE FUNCTION extract_feedback(decision)
EXTRACT_FEEDBACK_PROMPT = """\
From the following synthesizer output:
{decision}

Extract and return only the content that appears after "FEEDBACK: ".
Return just the feedback text with no additional prefix."""

# SPL: CREATE FUNCTION write_concise_report(topic, notes)
WRITE_CONCISE_REPORT_PROMPT = """\
Write a concise, well-structured research report on the following topic: {topic}

Use these accumulated research notes as your source material: {notes}

The report should include key findings, important insights, and a clear conclusion.
Be comprehensive yet concise."""


# ---------------------------------------------------------------------------
# Nodes — one per logical SPL step
# ---------------------------------------------------------------------------

class InitNode(Node):
    # SPL: @loop_count := 0; @feedback := ""; @notes := ""; @report := ""
    def exec(self, _):
        return None

    def post(self, shared, _, __):
        shared.setdefault("loop_count", 0)
        shared.setdefault("feedback", "")
        shared.setdefault("notes", "")
        shared.setdefault("report", "")
        return "default"


class PlannerNode(Node):
    # SPL: GENERATE planner(@topic, @feedback) INTO @queries
    def prep(self, shared):
        return shared["topic"], shared["feedback"]

    def exec(self, inputs):
        topic, feedback = inputs
        return call_llm(PLANNER_PROMPT.format(topic=topic, feedback=feedback))

    def post(self, shared, _, queries):
        shared["queries"] = queries
        return "default"


class LoopCheckNode(Node):
    # SPL: WHILE @loop_count < 3 DO / EVALUATE @loop_count WHEN contains("2")
    def prep(self, shared):
        return shared["loop_count"]

    def exec(self, loop_count):
        return loop_count

    def post(self, shared, _, loop_count):
        if loop_count >= 3:
            return "done"
        # SPL: EVALUATE @loop_count WHEN contains("2") THEN
        if "2" in str(loop_count):
            return "max_loops"
        return "continue"


class WriteConciseReportNode(Node):
    # SPL: GENERATE write_concise_report(@topic, @notes) INTO @report
    #      @loop_count := 3
    def prep(self, shared):
        return shared["topic"], shared["notes"]

    def exec(self, inputs):
        topic, notes = inputs
        return call_llm(WRITE_CONCISE_REPORT_PROMPT.format(topic=topic, notes=notes))

    def post(self, shared, _, report):
        shared["report"] = report
        shared["loop_count"] = 3
        return "default"


class ExtractQueriesNode(Node):
    # SPL: GENERATE extract_query(@queries, 1) INTO @query1
    #      GENERATE extract_query(@queries, 2) INTO @query2
    #      GENERATE extract_query(@queries, 3) INTO @query3
    def prep(self, shared):
        return shared["queries"]

    def exec(self, queries):
        def extract(pos):
            return call_llm(EXTRACT_QUERY_PROMPT.format(queries=queries, position=pos))

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            q1, q2, q3 = list(pool.map(extract, [1, 2, 3]))
        return q1, q2, q3

    def post(self, shared, _, results):
        shared["query1"], shared["query2"], shared["query3"] = results
        return "default"


class SearchWebNode(Node):
    # SPL: CALL PARALLEL
    #        search_web(@query1) INTO @result1,
    #        search_web(@query2) INTO @result2,
    #        search_web(@query3) INTO @result3
    #      END
    def prep(self, shared):
        return shared["query1"], shared["query2"], shared["query3"]

    def exec(self, inputs):
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            r1, r2, r3 = list(pool.map(search_web, inputs))
        return r1, r2, r3

    def post(self, shared, _, results):
        shared["result1"], shared["result2"], shared["result3"] = results
        return "default"


class ExtractFactsNode(Node):
    # SPL: CALL PARALLEL
    #        extract_facts(@query1, @result1) INTO @note1,
    #        extract_facts(@query2, @result2) INTO @note2,
    #        extract_facts(@query3, @result3) INTO @note3
    #      END
    def prep(self, shared):
        return (
            (shared["query1"], shared["result1"]),
            (shared["query2"], shared["result2"]),
            (shared["query3"], shared["result3"]),
        )

    def exec(self, pairs):
        def extract(pair):
            query, result = pair
            return call_llm(EXTRACT_FACTS_PROMPT.format(query=query, result=result))

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            n1, n2, n3 = list(pool.map(extract, pairs))
        return n1, n2, n3

    def post(self, shared, _, notes):
        shared["note1"], shared["note2"], shared["note3"] = notes
        return "default"


class AccumulateNotesNode(Node):
    # SPL: GENERATE accumulate_notes(@notes, @note1, @note2, @note3) INTO @notes
    def prep(self, shared):
        return shared["notes"], shared["note1"], shared["note2"], shared["note3"]

    def exec(self, inputs):
        existing, n1, n2, n3 = inputs
        return call_llm(
            ACCUMULATE_NOTES_PROMPT.format(
                existing_notes=existing, note1=n1, note2=n2, note3=n3
            )
        )

    def post(self, shared, _, notes):
        shared["notes"] = notes
        return "default"


class SynthesizerNode(Node):
    # SPL: GENERATE synthesizer(@topic, @notes, @loop_count) INTO @decision
    def prep(self, shared):
        return shared["topic"], shared["notes"], shared["loop_count"]

    def exec(self, inputs):
        topic, notes, loop_count = inputs
        return call_llm(
            SYNTHESIZER_PROMPT.format(topic=topic, notes=notes, loop_count=loop_count)
        )

    def post(self, shared, _, decision):
        shared["decision"] = decision
        return "default"


class EvaluateDecisionNode(Node):
    # SPL: EVALUATE @decision WHEN contains("DECISION: finalize") THEN ... ELSE ...
    def prep(self, shared):
        return shared["decision"]

    def exec(self, decision):
        return decision

    def post(self, shared, _, decision):
        if "DECISION: finalize" in decision:
            return "finalize"
        return "research"


class ExtractReportNode(Node):
    # SPL: GENERATE extract_report(@decision) INTO @report
    #      @loop_count := 3
    def prep(self, shared):
        return shared["decision"]

    def exec(self, decision):
        return call_llm(EXTRACT_REPORT_PROMPT.format(decision=decision))

    def post(self, shared, _, report):
        shared["report"] = report
        shared["loop_count"] = 3
        return "default"


class ExtractFeedbackNode(Node):
    # SPL: GENERATE extract_feedback(@decision) INTO @feedback
    #      @loop_count := @loop_count + 1
    #      GENERATE planner(@topic, @feedback) INTO @queries
    def prep(self, shared):
        return shared["decision"], shared["loop_count"], shared["topic"]

    def exec(self, inputs):
        decision, loop_count, topic = inputs
        feedback = call_llm(EXTRACT_FEEDBACK_PROMPT.format(decision=decision))
        new_count = loop_count + 1
        queries = call_llm(PLANNER_PROMPT.format(topic=topic, feedback=feedback))
        return feedback, new_count, queries

    def post(self, shared, _, results):
        shared["feedback"], shared["loop_count"], shared["queries"] = results
        return "default"


class WriteFileNode(Node):
    # SPL: CALL write_file(@out, @report) INTO @write_result
    def prep(self, shared):
        return shared.get("out", "report.txt"), shared["report"]

    def exec(self, inputs):
        path, content = inputs
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return f"written:{path}"

    def post(self, shared, _, write_result):
        # SPL: RETURN @report WITH status = "complete"
        shared["write_result"] = write_result
        return "default"


# ---------------------------------------------------------------------------
# Flow assembly — WORKFLOW deep_research
# ---------------------------------------------------------------------------

def build_flow() -> Flow:
    init          = InitNode()
    planner       = PlannerNode()
    loop_check    = LoopCheckNode()
    write_concise = WriteConciseReportNode()
    extract_qs    = ExtractQueriesNode()
    search        = SearchWebNode()
    facts         = ExtractFactsNode()
    accum         = AccumulateNotesNode()
    synth         = SynthesizerNode()
    eval_dec      = EvaluateDecisionNode()
    extract_rpt   = ExtractReportNode()
    extract_fb    = ExtractFeedbackNode()
    write_file    = WriteFileNode()

    # SPL: WORKFLOW deep_research — main spine
    init >> planner >> loop_check

    # SPL: WHILE @loop_count < 3 — exit when done
    loop_check - "done"      >> write_file

    # SPL: EVALUATE @loop_count WHEN contains("2") — max-iteration shortcut
    loop_check - "max_loops" >> write_concise >> write_file

    # SPL: normal research iteration path
    loop_check - "continue"  >> extract_qs >> search >> facts >> accum >> synth >> eval_dec

    # SPL: EVALUATE @decision WHEN contains("DECISION: finalize")
    eval_dec - "finalize"    >> extract_rpt >> write_file

    # SPL: ELSE — loop back for another iteration
    eval_dec - "research"    >> extract_fb >> loop_check

    return Flow(start=init)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_deep_research(topic: str, out: str = "report.txt") -> str:
    """Run the deep_research workflow and return the final report text."""
    shared = {"topic": topic, "out": out}
    build_flow().run(shared)
    return shared.get("report", "")


if __name__ == "__main__":
    _topic = sys.argv[1] if len(sys.argv) > 1 else "artificial intelligence in healthcare"
    _out   = sys.argv[2] if len(sys.argv) > 2 else "report.txt"
    print(run_deep_research(_topic, _out))