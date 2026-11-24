from __future__ import annotations

from click.testing import CliRunner

from spl3.cli import main
from spl3.docs.cli import STYLES, STYLES_DIR, WORKFLOW


def test_styles_and_workflow_ship_with_the_package():
    assert WORKFLOW.is_file()
    for s in STYLES:
        if s != "custom":
            assert (STYLES_DIR / f"{s}.md").is_file()
    assert (STYLES_DIR / "demo.template.html").is_file()


def test_docs_dry_run_reads_the_folder_and_calls_no_model(tmp_path):
    (tmp_path / "README.md").write_text("# Demo\nA tiny project.\n")
    res = CliRunner().invoke(main, ["docs", str(tmp_path), "--style", "tutorial,user-guide", "--dry-run", "--out-dir", str(tmp_path / "o")])
    assert res.exit_code == 0, res.output
    assert "dry run: nothing was run" in res.output and "README.md" in res.output
    assert not (tmp_path / "o").exists()


def test_docs_rejects_unknown_style_and_out_with_several_styles(tmp_path):
    r = CliRunner()
    assert r.invoke(main, ["docs", str(tmp_path), "--style", "nope"]).exit_code == 2
    assert r.invoke(main, ["docs", str(tmp_path), "--style", "demo,tutorial", "-o", "x.html"]).exit_code == 2


def test_the_workflow_validates():
    res = CliRunner().invoke(main, ["validate", str(WORKFLOW)])
    assert res.exit_code == 0, res.output
