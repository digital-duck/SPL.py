import click
from pathlib import Path
from flow import offline_flow, online_flow

# Sample documents kept in data/ — can be overridden via --input
DATA_DIR = Path(__file__).parent / "data"

DEFAULT_TEXTS = [
    "Pocket Flow is a 100-line minimalist LLM framework. "
    "Lightweight, zero bloat, zero dependencies, zero vendor lock-in. "
    "Install: pip install pocketflow",
    "NeurAlign M7 is a non-invasive neural alignment device. "
    "72% improvement in PTSD treatment outcomes. Developed by Cortex Medical in 2024.",
    "The Velvet Revolution of Caldonia (1967-1968) ended Generalissimo Verak's 40-year rule. "
    "Led by poet Eliza Markovian. First elections March 1968.",
    "Q-Mesh by QuantumLeap: 500k tx/s, 95% less energy than blockchain. Released Feb 2024.",
    "HI-271 fungi removes 99.7% of PFAS from soil in 60 days, 80% cheaper than chemicals.",
]


@click.command()
@click.option("--query", default="How to install PocketFlow?",
              show_default=True, help="Question to answer via RAG")
@click.option("--input", "input_path", default=None,
              help="Path to a text file to use as the document corpus (one doc per line)")
@click.option("--out", default=None,
              help="File path to save the answer (e.g. output/answer.md)")
def main(query, input_path, out):
    if input_path:
        p = Path(input_path)
        texts = [line.strip() for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
    else:
        texts = DEFAULT_TEXTS

    click.echo("=" * 50)
    click.echo("PocketFlow RAG Document Retrieval")
    click.echo(f"Documents: {len(texts)}  |  Query: {query}")
    click.echo("=" * 50)

    shared = {
        "texts": texts,
        "embeddings": None,
        "index": None,
        "query": query,
        "query_embedding": None,
        "retrieved_document": None,
        "generated_answer": None,
    }
    offline_flow.run(shared)
    online_flow.run(shared)

    answer = shared.get("generated_answer", "No answer generated.")
    click.echo(f"\nAnswer: {answer}")
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(f"Q: {query}\nA: {answer}\n", encoding="utf-8")
        click.echo(f"\n✅ Saved to: {out}")


if __name__ == "__main__":
    main()
