"""Write the income and spending report and print the two headline sentences."""

from isd181.ledger import find_root, load_context, load_lines, load_sources
from isd181.report import headline_sentences, render_html, render_markdown


def main() -> None:
    root = find_root()
    lines = load_lines(root)
    context = load_context(root)
    sources = load_sources(root)
    out_dir = root / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "income-spending.md").write_text(
        render_markdown(lines, context, sources), encoding="utf-8"
    )
    (out_dir / "income-spending.html").write_text(
        render_html(lines, context, sources), encoding="utf-8"
    )
    for sentence in headline_sentences(lines):
        print(sentence)


if __name__ == "__main__":
    main()
