import click
from pathlib import Path
from flow import create_deep_research_flow


@click.command()
@click.option("--topic", default="The current state of quantum computing in 2025",
              show_default=True, help="Topic to research")
@click.option("--out", default="output/report.md", show_default=True,
              help="File path to save the research report")
def main(topic, out):
    shared = {"topic": topic}
    click.echo(f"🤔 Researching: {topic}\n")
    create_deep_research_flow().run(shared)

    report = shared.get("report", "No report generated.")
    click.echo("\n📄 Final Report:\n")
    click.echo(report)

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(report, encoding="utf-8")
    click.echo(f"\n✅ Saved to: {out}")


if __name__ == "__main__":
    main()
