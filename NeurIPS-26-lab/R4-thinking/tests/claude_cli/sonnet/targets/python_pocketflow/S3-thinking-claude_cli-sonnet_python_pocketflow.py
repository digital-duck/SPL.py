#!/usr/bin/env python3
# S3-thinking-claude_cli-sonnet — compiled from S3-thinking-claude_cli-sonnet.spl
# Target: Python / PocketFlow

import subprocess
import sys
from typing import Any

import yaml
from pocketflow import Flow, Node

_MODEL = "claude-sonnet-4-6"
_MAX_YAML_RETRIES = 3


# ---------------------------------------------------------------------------
# SPL CALL helper functions
# ---------------------------------------------------------------------------

def _format_thoughts_to_text(thoughts: list) -> str:
    # SPL: CALL format_thoughts_to_text(@thoughts) INTO @thoughts_text
    if not thoughts:
        return "(no previous thoughts)"
    return "\n".join(
        f"Thought {i}: {t.get('current_thinking', '')}" for i, t in enumerate(thoughts, 1)
    )


def _extract_last_plan(thoughts: list) -> str:
    # SPL: CALL extract_last_plan(@thoughts) INTO @last_plan_text
    return thoughts[-1].get("next_action_plan", "(no plan yet)") if thoughts else "(no plan yet)"


def _validate_yaml_fields(text: str) -> str:
    # SPL: CALL validate_yaml_fields(@thought_data) INTO @yaml_valid
    required = {"current_thinking", "next_action_plan", "next_thought_needed"}
    try:
        data = yaml.safe_load(text)
        return "true" if isinstance(data, dict) and required.issubset(data) else "false"
    except Exception:
        return "false"


def _write_file(path: str, content: str, mode: str) -> None:
    # SPL: CALL write_file(@trace_file, ..., "a") INTO @_
    with open(path, mode, encoding="utf-8") as fh:
        fh.write(content)


def _append_thought(thoughts: list, yaml_text: str) -> list:
    # SPL: CALL append_thought(@thoughts, @thought_data) INTO @thoughts
    try:
        data = yaml.safe_load(yaml_text)
        thoughts.append(data if isinstance(data, dict) else {"raw": yaml_text})
    except Exception:
        thoughts.append({"raw": yaml_text})
    return thoughts


def _extract_yaml_field(text: str, field: str) -> str:
    # SPL: CALL extract_yaml_field(@thought_data, field) INTO @var
    try:
        data = yaml.safe_load(text)
        if isinstance(data, dict) and field in data:
            val = data[field]
            return str(val).lower() if isinstance(val, bool) else str(val)
    except Exception:
        pass
    return ""


def _print_thought_progress(thinking: str, plan: str) -> str:
    # SPL: CALL print_thought_progress(@current_thinking, @updated_plan) INTO @print_result
    print(f"\n[Thinking] {thinking[:200]}...")
    print(f"[Plan]     {plan[:200]}...")
    return "ok"


# ---------------------------------------------------------------------------
# SPL: CREATE FUNCTION ChainOfThoughtStep(problem, thoughts_text, last_plan, thought_number)
# ---------------------------------------------------------------------------

def _cot_prompt(problem: str, thoughts_text: str, last_plan: str, thought_number: int) -> str:
    return (
        "You are performing step-by-step chain of thought reasoning.\n\n"
        f"Problem: {problem}\n\n"
        f"Previous thoughts:\n{thoughts_text}\n\n"
        f"Last plan: {last_plan}\n\n"
        f"This is thought number {thought_number}.\n\n"
        "Respond with PLAIN YAML only — do NOT wrap in code fences or markdown blocks.\n"
        "Output exactly these required fields and nothing else:\n"
        "  current_thinking: your detailed analysis for this reasoning step\n"
        "  next_action_plan: your updated plan for the next step\n"
        "  next_thought_needed: true if more reasoning is needed, false if you have reached a complete conclusion"
    )


def _call_llm(prompt: str, model: str) -> str:
    # SPL: GENERATE ChainOfThoughtStep(...) INTO @thought_data  [claude_cli adapter]
    r = subprocess.run(
        ["claude", "--model", model, "-p", prompt, "--output-format", "text"],
        capture_output=True, text=True, check=True,
    )
    return r.stdout.strip()


# ---------------------------------------------------------------------------
# PocketFlow Nodes
# ---------------------------------------------------------------------------

class S3ThinkingInitNode(Node):
    # SPL: variable initialization block at WORKFLOW entry
    def prep(self, shared: dict) -> None:
        return None

    def exec(self, _: None) -> dict:
        # SPL: @thoughts:="[]"; @thought_number:=0; @solution:=""; @next_thought_needed:="true";
        #      @current_thinking:=""; @updated_plan:=""; @iteration:=0;
        return {
            "thoughts": [],
            "thought_number": 0,
            "solution": "",
            "next_thought_needed": "true",
            "current_thinking": "",
            "updated_plan": "",
            "iteration": 0,
        }

    def post(self, shared: dict, _: None, init_vals: dict) -> str:
        shared.update(init_vals)
        return "think"


class S3ThinkingThinkNode(Node):
    # SPL: WHILE @next_thought_needed="true" AND @iteration<@max_iterations DO ... END
    def prep(self, shared: dict) -> Any:
        # SPL: WHILE condition — evaluated before each loop body execution
        if shared["next_thought_needed"] != "true" or shared["iteration"] >= shared["max_iterations"]:
            return None
        return {
            "problem": shared["problem"],
            "trace_file": shared["trace_file"],
            "thoughts": list(shared["thoughts"]),
            "thought_number": shared["thought_number"],
            "iteration": shared["iteration"],
            "model": shared.get("model", _MODEL),
        }

    def exec(self, p: Any) -> Any:
        if p is None:
            return None

        # SPL: @thought_number := @thought_number + 1; @iteration := @iteration + 1;
        thought_number = p["thought_number"] + 1
        iteration = p["iteration"] + 1
        thoughts = p["thoughts"]

        # SPL: CALL format_thoughts_to_text(@thoughts) INTO @thoughts_text
        thoughts_text = _format_thoughts_to_text(thoughts)
        # SPL: CALL extract_last_plan(@thoughts) INTO @last_plan_text
        last_plan_text = _extract_last_plan(thoughts)

        # SPL: @retry_count:=0; @yaml_valid:="false";
        #      WHILE @yaml_valid="false" AND @retry_count<3 DO
        #        GENERATE ChainOfThoughtStep(...) INTO @thought_data;
        #        CALL validate_yaml_fields(@thought_data) INTO @yaml_valid;
        #        @retry_count := @retry_count + 1;
        #      END;
        retry_count, yaml_valid, thought_data = 0, "false", ""
        while yaml_valid == "false" and retry_count < _MAX_YAML_RETRIES:
            thought_data = _call_llm(
                _cot_prompt(p["problem"], thoughts_text, last_plan_text, thought_number),
                p["model"],
            )
            yaml_valid = _validate_yaml_fields(thought_data)
            retry_count += 1

        # SPL: CALL write_file(@trace_file, f'--- Thought {@thought_number} (yaml_valid={@yaml_valid}) ---\n{@thought_data}\n', "a") INTO @_
        _write_file(
            p["trace_file"],
            f"--- Thought {thought_number} (yaml_valid={yaml_valid}) ---\n{thought_data}\n",
            "a",
        )

        # SPL: CALL append_thought(@thoughts, @thought_data) INTO @thoughts
        thoughts = _append_thought(thoughts, thought_data)

        # SPL: CALL extract_yaml_field(@thought_data, "next_thought_needed") INTO @next_thought_needed
        next_thought_needed = _extract_yaml_field(thought_data, "next_thought_needed")
        # SPL: CALL extract_yaml_field(@thought_data, "current_thinking") INTO @current_thinking
        current_thinking = _extract_yaml_field(thought_data, "current_thinking")
        # SPL: CALL extract_yaml_field(@thought_data, "next_action_plan") INTO @updated_plan
        updated_plan = _extract_yaml_field(thought_data, "next_action_plan")

        # SPL: CALL write_file(@trace_file, f'next_thought_needed={@next_thought_needed}\ncurrent_thinking={@current_thinking}\n\n', "a") INTO @_
        _write_file(
            p["trace_file"],
            f"next_thought_needed={next_thought_needed}\ncurrent_thinking={current_thinking}\n\n",
            "a",
        )

        # SPL: CALL print_thought_progress(@current_thinking, @updated_plan) INTO @print_result
        _print_thought_progress(current_thinking, updated_plan)

        return {
            "thoughts": thoughts,
            "thought_number": thought_number,
            "iteration": iteration,
            "next_thought_needed": next_thought_needed,
            "current_thinking": current_thinking,
            "updated_plan": updated_plan,
        }

    def post(self, shared: dict, _: Any, exec_res: Any) -> str:
        if exec_res is None:
            return "done"   # SPL: WHILE condition false — exit loop
        shared.update(exec_res)
        return "continue"   # SPL: loop back to WHILE condition check


class S3ThinkingFinalizeNode(Node):
    # SPL: @solution := @current_thinking; RETURN @solution WITH status="complete"
    def prep(self, shared: dict) -> str:
        return shared.get("current_thinking", "")

    def exec(self, solution: str) -> str:
        return solution

    def post(self, shared: dict, _: str, solution: str) -> str:
        shared["solution"] = solution
        shared["status"] = "complete"
        return "end"


# ---------------------------------------------------------------------------
# Flow assembly
# ---------------------------------------------------------------------------

def _build_flow() -> Flow:
    # SPL: WORKFLOW ChainOfThought — node graph
    init = S3ThinkingInitNode()
    think = S3ThinkingThinkNode()
    finalize = S3ThinkingFinalizeNode()

    init - "think" >> think
    think - "continue" >> think   # SPL: WHILE loop back
    think - "done" >> finalize    # SPL: WHILE exit → finalize

    return Flow(start=init)


# ---------------------------------------------------------------------------
# Public API  (SPL WORKFLOW entry point)
# ---------------------------------------------------------------------------

def run_s3_thinking_chain_of_thought(
    problem: str,
    max_iterations: int = 5,
    trace_file: str = "chain_of_thought_trace.md",
    model: str = _MODEL,
) -> dict:
    # SPL: WORKFLOW ChainOfThought INPUT @problem TEXT, @max_iterations INT:=5, @trace_file TEXT:="chain_of_thought_trace.md"
    shared: dict = {
        "problem": problem,
        "max_iterations": max_iterations,
        "trace_file": trace_file,
        "model": model,
    }
    try:
        _build_flow().run(shared)
    except subprocess.CalledProcessError as exc:
        # SPL: EXCEPTION WHEN BudgetExceeded THEN RETURN @current_thinking WITH status="budget_limit"
        shared["solution"] = shared.get("current_thinking", "")
        shared["status"] = "budget_limit"
        print(f"[BudgetExceeded] {exc.stderr}", file=sys.stderr)
    return {"solution": shared.get("solution", ""), "status": shared.get("status", "unknown")}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        description="S3-thinking-claude_cli-sonnet: Chain of Thought via Claude CLI + PocketFlow"
    )
    ap.add_argument("problem", help="Problem or question to reason about")
    ap.add_argument("--max-iterations", type=int, default=5, metavar="N")
    ap.add_argument("--trace-file", default="chain_of_thought_trace.md", metavar="PATH")
    ap.add_argument("--model", default=_MODEL, metavar="MODEL")
    args = ap.parse_args()

    result = run_s3_thinking_chain_of_thought(
        args.problem, args.max_iterations, args.trace_file, args.model
    )
    print(f"\n{'='*60}\nSOLUTION (status={result['status']})\n{'='*60}\n{result['solution']}")