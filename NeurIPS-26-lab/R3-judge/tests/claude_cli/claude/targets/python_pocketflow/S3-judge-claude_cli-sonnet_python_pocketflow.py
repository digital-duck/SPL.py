#!/usr/bin/env python3
"""
S3-judge-claude_cli-sonnet.py
PocketFlow implementation compiled from S3-judge-claude_cli-sonnet.spl
"""

import subprocess
import sys
from pocketflow import Node, Flow

# SPL: WORKFLOW judge_workflow — model selection
MODEL = "claude-sonnet-4-6"

# SPL: WHILE @attempts < 3 — upper bound on retry iterations
MAX_ATTEMPTS = 3


def _call_llm(prompt: str) -> str:
    result = subprocess.run(
        ["claude", "-p", prompt, "--model", MODEL, "--output-format", "text"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


# SPL: CREATE FUNCTION generate_draft(task, feedback) RETURNS TEXT AS $$ ... $$
def _generate_draft(task: str, feedback: str) -> str:
    return _call_llm(
        f"You are a skilled writer. Generate a high-quality description for the following task: {task}\n"
        f"If feedback is provided, use it to improve this draft: {feedback}\n"
        "Produce a clear, detailed, and well-structured response. "
        "Don't simply repeat the task description verbatim."
    )


# SPL: CREATE FUNCTION evaluate_draft(task, draft) RETURNS TEXT AS $$ ... $$
def _evaluate_draft(task: str, draft: str) -> str:
    return _call_llm(
        "You are a strict quality judge. Evaluate the draft below against the task requirements.\n"
        f"Task: {task}\n"
        f"Draft: {draft}\n"
        "Score the draft on accuracy, clarity, completeness, and overall quality (scale 1-10).\n"
        "If the score is 7 or above, respond with: VERDICT: PASS, Score: [score], Feedback: [brief comment]\n"
        "If the score is below 7, respond with: VERDICT: FAIL, Score: [score], "
        "Feedback: [specific actionable suggestions for improvement]"
    )


class GenerateDraftNode(Node):
    # SPL: GENERATE generate_draft(@task, @feedback) INTO @draft

    def prep(self, shared: dict):
        return shared["task"], shared["feedback"]

    def exec(self, inputs):
        task, feedback = inputs
        return _generate_draft(task, feedback)

    def post(self, shared: dict, prep_res, exec_res: str):
        shared["draft"] = exec_res
        return "default"


class EvaluateDraftNode(Node):
    # SPL: GENERATE evaluate_draft(@task, @draft) INTO @judgment

    def prep(self, shared: dict):
        return shared["task"], shared["draft"]

    def exec(self, inputs):
        task, draft = inputs
        return _evaluate_draft(task, draft)

    def post(self, shared: dict, prep_res, exec_res: str):
        shared["judgment"] = exec_res
        return "default"


class CheckVerdictNode(Node):
    """
    SPL: EVALUATE @judgment
           WHEN contains("VERDICT: PASS") THEN
             @final_description := @draft; RETURN WITH status="pass"
           ELSE
             @attempts := @attempts + 1; @feedback := @judgment
         END
         (also enforces: WHILE @attempts < 3)
    """

    def prep(self, shared: dict):
        return shared["judgment"], shared["attempts"], shared["draft"]

    def exec(self, inputs):
        judgment, attempts, draft = inputs
        return "VERDICT: PASS" in judgment, attempts, draft

    def post(self, shared: dict, prep_res, exec_res):
        passed, attempts, draft = exec_res
        judgment = shared["judgment"]

        # SPL: WHEN contains("VERDICT: PASS") THEN
        if passed:
            # SPL: @final_description := @draft; @final_score := @judgment
            shared["final_description"] = draft
            shared["final_score"] = judgment
            # SPL: RETURN @final_description WITH status = "pass"
            shared["status"] = "pass"
            return "pass"

        # SPL: ELSE @attempts := @attempts + 1; @feedback := @judgment
        attempts += 1
        shared["attempts"] = attempts
        shared["feedback"] = judgment

        # SPL: WHILE @attempts < 3 DO ... END
        if attempts < MAX_ATTEMPTS:
            return "retry"

        # SPL: (post-WHILE) @final_description := @draft
        # SPL: RETURN @final_description WITH status = "max_attempts"
        shared["final_description"] = draft
        shared["final_score"] = judgment
        shared["status"] = "max_attempts"
        return "max_attempts"


def build_flow() -> Flow:
    generate = GenerateDraftNode()
    evaluate = EvaluateDraftNode()
    check = CheckVerdictNode()

    # SPL: GENERATE → GENERATE → EVALUATE/WHILE loop
    generate >> evaluate >> check

    # SPL: ELSE branch — loop back to GENERATE for refinement
    check - "retry" >> generate

    # "pass" and "max_attempts" are terminal; no outgoing edges needed
    return Flow(start=generate)


def run_judge_workflow(task: str) -> dict:
    """
    SPL: WORKFLOW judge_workflow
           INPUT  @task TEXT
           OUTPUT @final_description TEXT
    """
    # SPL: @feedback := ""; @attempts := 0; @final_description := ""; @final_score := ""
    shared = {
        "task": task,
        "feedback": "",
        "attempts": 0,
        "draft": "",
        "judgment": "",
        "final_description": "",
        "final_score": "",
        "status": "max_attempts",
    }

    build_flow().run(shared)

    return {
        "final_description": shared["final_description"],
        "final_score": shared["final_score"],
        "status": shared["status"],
        "attempts": shared["attempts"],
    }


if __name__ == "__main__":
    task = sys.argv[1] if len(sys.argv) > 1 else "explain the water cycle"

    print(f"Task      : {task}\n")
    result = run_judge_workflow(task)
    print(f"Status    : {result['status']}")
    print(f"Attempts  : {result['attempts']}")
    print(f"\n--- Final Description ---\n{result['final_description']}")
    print(f"\n--- Final Score ---\n{result['final_score']}")