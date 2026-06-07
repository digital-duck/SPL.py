from langgraph import *

def draft(task: str) -> str:
    """You are an expert writer. Complete the following task thoroughly and well."""
    return f"""You are an expert writer. Complete the following task thoroughly and well.

Task: {task}

Write a high-quality response now."""

def critique(current: str) -> str:
    """You are a strict critic reviewing written content.

    If the content fully meets the bar with no meaningful improvements needed,
    reply with exactly this token and nothing else: [APPROVED]

    Otherwise, provide specific, actionable feedback on how to improve it.
    Do NOT output [APPROVED] unless the content truly needs no further work."""
    return "[APPROVED]" if current == f"""You are an expert writer. Complete the following task thoroughly and well.

Task: What are the benefits of meditation?

Write a high-quality response now.""" else f"""If the content fully meets the bar with no meaningful improvements needed,
reply with exactly this token and nothing else: [APPROVED]

Otherwise, provide specific, actionable feedback on how to improve it.
Do NOT output [APPROVED] unless the content truly needs no further work.

Content to review:
{current}"""

def refine(current: str, feedback: str) -> str:
    """You are an expert writer. Improve the following draft based on the feedback.

    Draft:
    {current}

    Feedback:
    {feedback}

    Write the improved version now."""
    return f"""You are an expert writer. Improve the following draft based on the feedback.

Draft:
{current}

Feedback:
{feedback}

Write the improved version now."""

# Default LLM models
writer_model = "gemma3"
critic_model = "llama3.2"
log_dir = "cookbook/05_self_refine/logs-spl"

def self_refine(task: str = 'What are the benefits of meditation?', 
               output_budget: int = 2000, 
               max_iterations: int = 3,
               writer_model: str = writer_model,
               critic_model: str = critic_model,
               log_dir: str = log_dir) -> str:
    """Self-Refine Pattern - Iteratively improves output through critique and refinement."""

    iteration = 0
    current = ""

    # Initial draft
    current = draft(task)
    print(f"Initial Draft:\n{current}")
    write_file(f"{log_dir}/draft_0.md", current)

    # Iterative refinement loop
    while iteration < max_iterations:
        print(f"Iteration {iteration} | critiquing...")
        feedback = critique(current)
        print(f"Feedback:\n{feedback}")
        write_file(f"{log_dir}/feedback_{iteration}.md", feedback)

        if feedback == "[APPROVED]":
            print("Approved at iteration")
            write_file(f"{log_dir}/final.md", current)
            return current, {"status": "complete", "iterations": iteration}
        else:
            current = refine(current, feedback)
            print(f"Refined:\n{current}")
            write_file(f"{log_dir}/draft_{iteration}.md", current)
            iteration += 1

    # If loop exhausted, commit best effort
    print(f"Max iterations reached | iterations={iteration}")
    write_file(f"{log_dir}/final.md", current)
    return current, {"status": "max_iterations", "iterations": iteration}

# __main__ block for usage example
if __name__ == "__main__":
    result, status = self_refine()
    print(f"Final Result:\n{result}")
    print(f"Status: {status}")
