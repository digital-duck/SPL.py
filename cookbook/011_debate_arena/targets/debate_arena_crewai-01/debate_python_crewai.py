#!/usr/bin/env python3
"""
debate.py — CrewAI implementation compiled from debate.spl
SPL Recipe: Debate Arena
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from crewai import Agent, Crew, Task

# ---------------------------------------------------------------------------
# Logging  (SPL: LOGGING ... LEVEL INFO / DEBUG)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("debate_arena")


# ---------------------------------------------------------------------------
# SPL exception types  (SPL: EXCEPTION WHEN ExceptionType THEN)
# ---------------------------------------------------------------------------
class MaxIterationsReached(Exception):
    """SPL: EXCEPTION WHEN MaxIterationsReached"""

class BudgetExceeded(Exception):
    """SPL: EXCEPTION WHEN BudgetExceeded"""


# ---------------------------------------------------------------------------
# SPL: CALL write_file(path, content) INTO NONE
# ---------------------------------------------------------------------------
def _write_file(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# SPL: CREATE FUNCTION prompts  →  prompt templates bound at call time
# ---------------------------------------------------------------------------

# SPL: CREATE FUNCTION pro_argument(topic TEXT, previous TEXT) RETURNS TEXT AS $$ ... $$
_PRO_ARGUMENT_TMPL = """\
You are a skilled debate champion arguing STRONGLY IN FAVOR of the following motion:

Motion: "{topic}"

Your opponent's last argument (or "opening statement" if this is your first turn):
{previous}

Write a focused, persuasive argument supporting the motion. If this is a rebuttal round,
directly address and counter your opponent's points. Be concise (3-5 paragraphs).
Do NOT offer balanced views — you are arguing one side."""

# SPL: CREATE FUNCTION con_argument(topic TEXT, previous TEXT) RETURNS TEXT AS $$ ... $$
_CON_ARGUMENT_TMPL = """\
You are a skilled debate champion arguing STRONGLY AGAINST the following motion:

Motion: "{topic}"

Your opponent's last argument (or "opening statement" if this is your first turn):
{previous}

Write a focused, persuasive argument opposing the motion. If this is a rebuttal round,
directly address and counter your opponent's points. Be concise (3-5 paragraphs).
Do NOT offer balanced views — you are arguing one side."""

# SPL: CREATE FUNCTION judge_debate(topic TEXT, pro_history TEXT, con_history TEXT) RETURNS TEXT AS $$ ... $$
_JUDGE_TMPL = """\
You are an impartial debate judge evaluating the following debate.

Motion: "{topic}"

--- PRO SIDE (arguing IN FAVOR) ---
{pro_history}

--- CON SIDE (arguing AGAINST) ---
{con_history}

Evaluate the debate on these criteria:
1. Strength of arguments
2. Quality of rebuttals
3. Clarity and persuasiveness

Declare a winner (PRO or CON) and explain your reasoning in 2-3 paragraphs."""


# ---------------------------------------------------------------------------
# SPL: GENERATE function(...) INTO @var
# Wraps a single agent call as a minimal one-task Crew.
# ---------------------------------------------------------------------------
def _generate(agent: Agent, prompt: str) -> str:
    task = Task(
        description=prompt,
        expected_output="A prose response fulfilling the prompt above.",
        agent=agent,
    )
    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    # CrewOutput.raw is the canonical string accessor in crewai >= 0.70
    return result.raw if hasattr(result, "raw") else str(result)


# ---------------------------------------------------------------------------
# SPL: WORKFLOW debate_arena
# ---------------------------------------------------------------------------
def debate_arena(
    topic: str = "AI should be open-sourced",              # SPL: @topic TEXT DEFAULT '...'
    max_rounds: int = 3,                                    # SPL: @max_rounds INTEGER DEFAULT 3
    log_dir: str = "cookbook/11_debate_arena/logs-crewai", # SPL: @log_dir TEXT DEFAULT '...'
    model: str = "ollama/gemma3",
) -> dict:
    """
    SPL: WORKFLOW debate_arena
      INPUT:  @topic TEXT, @max_rounds INTEGER, @log_dir TEXT
      OUTPUT: @verdict TEXT
    """

    # -- Agents (SPL: CREATE FUNCTION → Agent) --------------------------------

    # SPL: CREATE FUNCTION pro_argument  →  pro_agent
    pro_agent = Agent(
        role="Pro Debater",
        goal=f"Argue powerfully IN FAVOR of the motion: {topic}",
        backstory=(
            "You are a champion debater known for razor-sharp pro arguments. "
            "You never concede ground and always rebut directly."
        ),
        llm=model,
        verbose=False,
    )

    # SPL: CREATE FUNCTION con_argument  →  con_agent
    con_agent = Agent(
        role="Con Debater",
        goal=f"Argue powerfully AGAINST the motion: {topic}",
        backstory=(
            "You are a champion debater renowned for dismantling any proposition. "
            "You never concede ground and always rebut directly."
        ),
        llm=model,
        verbose=False,
    )

    # SPL: CREATE FUNCTION judge_debate  →  judge_agent
    judge_agent = Agent(
        role="Debate Judge",
        goal="Impartially evaluate both sides and declare a winner.",
        backstory=(
            "You are a seasoned, impartial debate judge with decades of experience "
            "in academic and policy debates."
        ),
        llm=model,
        verbose=False,
    )

    # -- Variable initialisation (SPL: @round := 0 / @pro_history := '' / @con_history := '')
    round_num: int = 0
    pro_history: str = ""
    con_history: str = ""
    verdict: str = ""

    # SPL: LOGGING f'Debate started | topic: {@topic} | rounds: {@max_rounds}' LEVEL INFO
    log.info("Debate started | topic: %s | rounds: %d", topic, max_rounds)

    try:
        # -- Opening statements -----------------------------------------------

        # SPL: GENERATE pro_argument(@topic, 'opening statement') INTO @pro
        pro: str = _generate(
            pro_agent,
            _PRO_ARGUMENT_TMPL.format(topic=topic, previous="opening statement"),
        )

        # SPL: GENERATE con_argument(@topic, 'opening statement') INTO @con
        con: str = _generate(
            con_agent,
            _CON_ARGUMENT_TMPL.format(topic=topic, previous="opening statement"),
        )

        # SPL: @pro_history := @pro  /  @con_history := @con
        pro_history = pro
        con_history = con

        # SPL: LOGGING 'Opening statements complete' LEVEL INFO
        log.info("Opening statements complete")

        # SPL: CALL write_file(f'{@log_dir}/opening_pro.md', @pro) INTO NONE
        _write_file(f"{log_dir}/opening_pro.md", pro)
        # SPL: CALL write_file(f'{@log_dir}/opening_con.md', @con) INTO NONE
        _write_file(f"{log_dir}/opening_con.md", con)

        # -- Rebuttal rounds (SPL: WHILE @round < @max_rounds DO ... END) -----
        while round_num < max_rounds:

            # SPL: LOGGING f'Round {@round} | pro rebuttal ...' LEVEL DEBUG
            log.debug("Round %d | pro rebuttal ...", round_num)

            # SPL: GENERATE pro_argument(@topic, @con_history) INTO @pro_rebuttal
            pro_rebuttal: str = _generate(
                pro_agent,
                _PRO_ARGUMENT_TMPL.format(topic=topic, previous=con_history),
            )
            # SPL: @pro_history := @pro_history || '\n---\n' || @pro_rebuttal
            pro_history = pro_history + "\n---\n" + pro_rebuttal
            # SPL: CALL write_file(f'{@log_dir}/round_{@round}_pro.md', @pro_rebuttal) INTO NONE
            _write_file(f"{log_dir}/round_{round_num}_pro.md", pro_rebuttal)

            # SPL: LOGGING f'Round {@round} | con rebuttal ...' LEVEL DEBUG
            log.debug("Round %d | con rebuttal ...", round_num)

            # SPL: GENERATE con_argument(@topic, @pro_history) INTO @con_rebuttal
            con_rebuttal: str = _generate(
                con_agent,
                _CON_ARGUMENT_TMPL.format(topic=topic, previous=pro_history),
            )
            # SPL: @con_history := @con_history || '\n---\n' || @con_rebuttal
            con_history = con_history + "\n---\n" + con_rebuttal
            # SPL: CALL write_file(f'{@log_dir}/round_{@round}_con.md', @con_rebuttal) INTO NONE
            _write_file(f"{log_dir}/round_{round_num}_con.md", con_rebuttal)

            # SPL: @round := @round + 1
            round_num += 1
            # SPL: LOGGING f'Round {@round} complete' LEVEL INFO
            log.info("Round %d complete", round_num)

        # -- Judge deliberation -----------------------------------------------

        # SPL: LOGGING 'All rounds done — judge deliberating ...' LEVEL INFO
        log.info("All rounds done — judge deliberating ...")

        # SPL: GENERATE judge_debate(@topic, @pro_history, @con_history) INTO @verdict
        verdict = _generate(
            judge_agent,
            _JUDGE_TMPL.format(
                topic=topic, pro_history=pro_history, con_history=con_history
            ),
        )

        # SPL: LOGGING f'Verdict ready | rounds={@round}' LEVEL INFO
        log.info("Verdict ready | rounds=%d", round_num)

        # SPL: CALL write_file(f'{@log_dir}/verdict.md', @verdict) INTO NONE
        _write_file(f"{log_dir}/verdict.md", verdict)

        # SPL: RETURN @verdict WITH status = 'complete', rounds = @round
        return {"output": verdict, "status": "complete", "rounds": round_num}

    # SPL: EXCEPTION WHEN MaxIterationsReached THEN
    except MaxIterationsReached:
        log.warning("MaxIterationsReached — running judge on partial history")
        # SPL: GENERATE judge_debate(@topic, @pro_history, @con_history) INTO @verdict
        verdict = _generate(
            judge_agent,
            _JUDGE_TMPL.format(
                topic=topic, pro_history=pro_history, con_history=con_history
            ),
        )
        # SPL: RETURN @verdict WITH status = 'partial'
        return {"output": verdict, "status": "partial", "rounds": round_num}

    # SPL: EXCEPTION WHEN BudgetExceeded THEN
    except BudgetExceeded:
        log.warning("BudgetExceeded — returning partial pro history")
        # SPL: RETURN @pro_history WITH status = 'budget_limit'
        return {"output": pro_history, "status": "budget_limit", "rounds": round_num}


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Debate Arena — CrewAI")
    parser.add_argument(
        "--topic", default="AI should be open-sourced", help="Debate motion"
    )
    parser.add_argument(
        "--max-rounds", type=int, default=3, help="Number of rebuttal rounds"
    )
    parser.add_argument(
        "--log-dir",
        default="cookbook/11_debate_arena/logs-crewai",
        help="Directory for per-round logs and verdict",
    )
    parser.add_argument(
        "--model",
        default="ollama/gemma3",
        help="LLM model string in CrewAI format (e.g. ollama/gemma3, openai/gpt-4o)",
    )
    args = parser.parse_args()

    result = debate_arena(
        topic=args.topic,
        max_rounds=args.max_rounds,
        log_dir=args.log_dir,
        model=args.model,
    )

    print("\n" + "=" * 60)
    print(f"STATUS : {result['status']}")
    print(f"ROUNDS : {result['rounds']}")
    print("=" * 60)
    print(result["output"])
