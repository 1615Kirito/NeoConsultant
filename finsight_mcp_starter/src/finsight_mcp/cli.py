#Define the command of the whole workflow.

#Example:
# @app.command()
# def report(
#     ticker: str,
#     output: Path = typer.Option(Path("output/report.json"), help="Output JSON path."),
# ) -> None:
#     """Generate one evidence-grounded LLM research report."""
#     result = asyncio.run(generate_report(ticker))
#     output.parent.mkdir(parents=True, exist_ok=True)
#     output.write_text(result.model_dump_json(indent=2), encoding="utf-8")
#     coverage = claim_level_citation_coverage(result)
#     typer.echo(f"Saved {output}")
#     typer.echo(f"Score: {result.score:.2f} | Citation coverage: {coverage:.1%}")
#     typer.echo(f"Citation IDs resolve: {citations_resolve(result)}")