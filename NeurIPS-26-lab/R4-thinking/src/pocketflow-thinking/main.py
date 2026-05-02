import click
from flow import create_chain_of_thought_flow

DEFAULT_QUESTION = (
    "You keep rolling a fair die until you roll three, four, five in that order "
    "consecutively on three rolls. What is the probability that you roll the die "
    "an odd number of times?"
)


@click.command()
@click.option("--question", default=DEFAULT_QUESTION, show_default=False,
              help="Reasoning problem to solve (default: dice probability puzzle)")
@click.option("--out", default=None, help="File path to save the solution (e.g. output/solution.md)")
def main(question, out):
    click.echo(f"🤔 Processing question: {question}")
    shared = {
        "problem": question,
        "thoughts": [],
        "current_thought_number": 0,
        "total_thoughts_estimate": 10,
        "solution": None,
    }
    create_chain_of_thought_flow().run(shared)
    if out and shared.get("solution"):
        from pathlib import Path
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(f"Q: {question}\n\n{shared['solution']}\n", encoding="utf-8")
        click.echo(f"\n✅ Saved to: {out}")


if __name__ == "__main__":
    main()
