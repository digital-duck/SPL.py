#!/usr/bin/env python3
"""
debate.py — CrewAI implementation compiled from debate.spl
Recipe: Debate Arena
"""

# SPL: WORKFLOW debate_arena
# SPL: CREATE FUNCTION pro_argument / con_argument / judge_debate

import logging
import sys
from pathlib import Path

from crewai import Agent, Crew, Task, Process

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-7s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# SPL: EXCEPTION WHEN MaxIterationsReached / BudgetExceeded
class MaxIterationsReached(Exception):
    pass


class BudgetExceeded(Exception):
    pass


# ── Helpers ────────────────────────────────────────────────────────────────

def _write_file(path: str, content: str) -> None:
    # SPL: CALL write_file(path, content) INTO NONE
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _run_task(agent: Agent, description: str) -> str:
    """Spin up a minimal single-task Crew and return the raw text output."""
    task = Task(
        description=description,
        agent=agent,
        expected_output="A well-structured text response.",
    )
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )
    result = crew.kickoff()
    return str(result)


# ── Agent factories (SPL: CREATE FUNCTION ... AS $$ prompt $$) ────────────

def _pro_agent(llm=None) -> Agent:
    # SPL: CREATE FUNCTION pro_argument(topic TEXT, previous TEXT)
    return Agent(
        role="Pro Debater",
        goal="Argue STRONGLY IN FAVOR of the motion with focused, persuasive points.",
        backstory=(
            "You are a skilled debate champion who always argues in favour of the motion. "
            "You never offer balanced views — you are arguing one side only."
        ),
        verbose=False,
        **({"llm": llm} if llm else {}),
    )


def _con_agent(llm=None) -> Agent:
    # SPL: CREATE FUNCTION con_argument(topic TEXT, previous TEXT)
    return Agent(
        role="Con Debater",
        goal="Argue STRONGLY AGAINST the motion with focused, persuasive points.",
        backstory=(
            "You are a skilled debate champion who always argues against the motion. "
            "You never offer balanced views — you are arguing one side only."
        ),
        verbose=False,
        **({"llm": llm} if llm else {}),
    )


def _judge_agent(llm=None) -> Agent:
    # SPL: CREATE FUNCTION judge_debate(topic TEXT, pro_history TEXT, con_history TEXT)
    return Agent(
        role="Debate Judge",
        goal="Impartially evaluate both sides and declare a winner (PRO or CON).",
        backstory=(
            "You are an impartial judge. You assess argument strength, rebuttal quality, "
            "and persuasiveness, then declare a clear winner with a reasoned explanation."
        ),
        verbose=False,
        **({"llm": llm} if llm else {}),
    )


# ── Prompt builders (mirror SPL function bodies verbatim) ─────────────────

def _pro_prompt(topic: str, previous: str) -> str:
    # SPL: CREATE FUNCTION pro_argument — AS $$ ... $$
    return f"""You are a skilled debate champion arguing STRONGLY IN FAVOR of the following motion:

Motion: "{topic}"

Your opponent's last argument (or "opening statement" if this is your first turn):
{previous}

Write a focused, persuasive argument supporting the motion. If this is a rebuttal round,
directly address and counter your opponent's points. Be concise (3-5 paragraphs).
Do NOT offer balanced views — you are arguing one side."""


def _con_prompt(topic: str, previous: str) -> str:
    # SPL: CREATE FUNCTION con_argument — AS $$ ... $$
    return f"""You are a skilled debate champion arguing STRONGLY AGAINST the following motion:

Motion: "{topic}"

Your opponent's last argument (or "opening statement" if this is your first turn):
{previous}

Write a focused, persuasive argument opposing the motion. If this is a rebuttal round,
directly address and counter your opponent's points. Be concise (3-5 paragraphs).
Do NOT offer balanced views — you are arguing one side."""


def _judge_prompt(topic: str, pro_history: str, con_history: str) -> str:
    # SPL: CREATE FUNCTION judge_debate — AS $$ ... $$
    return f"""You are an impartial debate judge evaluating the following debate.

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


# ── Workflow ───────────────────────────────────────────────────────────────

def debate_arena(
    topic: str = "AI should be open-sourced",           # SPL: @topic TEXT DEFAULT ...
    max_rounds: int = 3,                                 # SPL: @max_rounds INTEGER DEFAULT 3
    log_dir: str = "cookbook/11_debate_arena/logs-crewai",  # SPL: @log_dir TEXT DEFAULT ...
    llm=None,
) -> dict:
    """
    SPL: WORKFLOW debate_arena
         INPUT:  @topic, @max_rounds, @log_dir
         OUTPUT: @verdict TEXT
    """
    # SPL: @round := 0 / @pro_history := '' / @con_history := ''
    # Initialised before try so exception handlers can reference them safely.
    round_num: int = 0
    pro_history: str = ""
    con_history: str = ""

    pro_agent   = _pro_agent(llm)
    con_agent   = _con_agent(llm)
    judge       = _judge_agent(llm)

    try:
        # SPL: LOGGING f'Debate started | topic: {@topic} | rounds: {@max_rounds}' LEVEL INFO
        logger.info("Debate started | topic: %s | rounds: %d", topic, max_rounds)

        # ── Opening statements ────────────────────────────────────────────
        # SPL: GENERATE pro_argument(@topic, 'opening statement') INTO @pro
        pro = _run_task(pro_agent, _pro_prompt(topic, "opening statement"))

        # SPL: GENERATE con_argument(@topic, 'opening statement') INTO @con
        con = _run_task(con_agent, _con_prompt(topic, "opening statement"))

        # SPL: @pro_history := @pro / @con_history := @con
        pro_history = pro
        con_history = con

        # SPL: LOGGING 'Opening statements complete' LEVEL INFO
        logger.info("Opening statements complete")

        # SPL: CALL write_file(f'{@log_dir}/opening_pro.md', @pro) INTO NONE
        _write_file(f"{log_dir}/opening_pro.md", pro)
        # SPL: CALL write_file(f'{@log_dir}/opening_con.md', @con) INTO NONE
        _write_file(f"{log_dir}/opening_con.md", con)

        # ── Rebuttal rounds ───────────────────────────────────────────────
        # SPL: WHILE @round < @max_rounds DO ... END
        while round_num < max_rounds:

            # SPL: LOGGING f'Round {@round} | pro rebuttal ...' LEVEL DEBUG
            logger.debug("Round %d | pro rebuttal ...", round_num)

            # SPL: GENERATE pro_argument(@topic, @con_history) INTO @pro_rebuttal
            pro_rebuttal = _run_task(pro_agent, _pro_prompt(topic, con_history))

            # SPL: @pro_history := @pro_history || '\n---\n' || @pro_rebuttal
            pro_history = pro_history + "\n---\n" + pro_rebuttal

            # SPL: CALL write_file(f'{@log_dir}/round_{@round}_pro.md', @pro_rebuttal) INTO NONE
            _write_file(f"{log_dir}/round_{round_num}_pro.md", pro_rebuttal)

            # SPL: LOGGING f'Round {@round} | con rebuttal ...' LEVEL DEBUG
            logger.debug("Round %d | con rebuttal ...", round_num)

            # SPL: GENERATE con_argument(@topic, @pro_history) INTO @con_rebuttal
            con_rebuttal = _run_task(con_agent, _con_prompt(topic, pro_history))

            # SPL: @con_history := @con_history || '\n---\n' || @con_rebuttal
            con_history = con_history + "\n---\n" + con_rebuttal

            # SPL: CALL write_file(f'{@log_dir}/round_{@round}_con.md', @con_rebuttal) INTO NONE
            _write_file(f"{log_dir}/round_{round_num}_con.md", con_rebuttal)

            # SPL: @round := @round + 1
            round_num += 1

            # SPL: LOGGING f'Round {@round} complete' LEVEL INFO
            logger.info("Round %d complete", round_num)

        # ── Judging ───────────────────────────────────────────────────────
        # SPL: LOGGING 'All rounds done — judge deliberating ...' LEVEL INFO
        logger.info("All rounds done — judge deliberating ...")

        # SPL: GENERATE judge_debate(@topic, @pro_history, @con_history) INTO @verdict
        verdict = _run_task(judge, _judge_prompt(topic, pro_history, con_history))

        # SPL: LOGGING f'Verdict ready | rounds={@round}' LEVEL INFO
        logger.info("Verdict ready | rounds=%d", round_num)

        # SPL: CALL write_file(f'{@log_dir}/verdict.md', @verdict) INTO NONE
        _write_file(f"{log_dir}/verdict.md", verdict)

        # SPL: RETURN @verdict WITH status = 'complete', rounds = @round
        return {"verdict": verdict, "status": "complete", "rounds": round_num}

    # SPL: EXCEPTION WHEN MaxIterationsReached THEN
    except MaxIterationsReached:
        logger.warning("MaxIterationsReached — running emergency judgement")
        verdict = _run_task(judge, _judge_prompt(topic, pro_history, con_history))
        # SPL: RETURN @verdict WITH status = 'partial'
        return {"verdict": verdict, "status": "partial", "rounds": round_num}

    # SPL: EXCEPTION WHEN BudgetExceeded THEN
    except BudgetExceeded:
        logger.warning("BudgetExceeded — returning pro transcript as-is")
        # SPL: RETURN @pro_history WITH status = 'budget_limit'
        return {"verdict": pro_history, "status": "budget_limit", "rounds": round_num}


# ── CLI entry point ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Debate Arena — CrewAI")
    ap.add_argument("--topic",      default="AI should be open-sourced")
    ap.add_argument("--max-rounds", type=int, default=3)
    ap.add_argument("--log-dir",    default="cookbook/11_debate_arena/logs-crewai")
    ap.add_argument(
        "--model",
        default=None,
        help="CrewAI LLM model string, e.g. 'ollama/gemma3' or 'openai/gpt-4o'",
    )
    args = ap.parse_args()

    llm = None
    if args.model:
        from crewai import LLM
        llm = LLM(model=args.model)

    result = debate_arena(
        topic=args.topic,
        max_rounds=args.max_rounds,
        log_dir=args.log_dir,
        llm=llm,
    )

    print("\n" + "=" * 60)
    print(f"Status : {result['status']}")
    print(f"Rounds : {result['rounds']}")
    print("=" * 60)
    print(result["verdict"])