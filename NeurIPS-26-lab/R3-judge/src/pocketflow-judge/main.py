import click
from flow import create_judge_flow


@click.command()
@click.option("--task", default="A noise-cancelling wireless headphone with 30-hour battery life",
              show_default=True, help="Product to generate and judge a description for")
@click.option("--out", default=None, help="File path to save the result (e.g. output/result.md)")
def main(task, out):
    click.echo(f"🤔 Generating product description for: {task}")
    shared = {"task": task, "attempts": 0}
    create_judge_flow().run(shared)

    description = shared.get("final_description", "N/A")
    score = shared.get("final_score", "N/A")
    click.echo("\n=== Final Result ===")
    click.echo(f"📝 Description: {description}")
    click.echo(f"⭐ Score:       {score}/10")
    click.echo("====================")
    if out:
        from pathlib import Path
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(f"Task: {task}\nScore: {score}/10\n\n{description}\n", encoding="utf-8")
        click.echo(f"\n✅ Saved to: {out}")


if __name__ == "__main__":
    main()
