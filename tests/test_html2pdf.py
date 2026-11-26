"""spl3 util html2pdf: a thin wrapper over dd-format's html_to_pdf; the browser is faked (no Chromium needed). The conversion itself is tested in dd-format."""
import stat

import pytest
from click.testing import CliRunner

pytest.importorskip("dd_format", reason="spl3 util html2pdf needs dd-format (pip install 'spl-llm[format]')")

from spl3.cli import main  # noqa: E402

FAKE = """#!/usr/bin/env bash
for a in "$@"; do case "$a" in --print-to-pdf=*) out="${a#--print-to-pdf=}";; esac; done
printf '%%PDF-1.4\\n/Type /Page\\n/Type /Page\\n/Type /Pages\\n' > "$out"
"""


@pytest.fixture
def fake_browser(tmp_path, monkeypatch):
    exe = tmp_path / "fakechrome"
    exe.write_text(FAKE)
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("CHROME", str(exe))
    return exe


def test_cli_output_option_and_missing_input(tmp_path, fake_browser):
    deck = tmp_path / "deck.html"
    deck.write_text("<html></html>")
    r = CliRunner().invoke(main, ["util", "html2pdf", str(deck), "-o", str(tmp_path / "sub" / "x.pdf")])
    assert r.exit_code == 0 and "2 pages" in r.output and (tmp_path / "sub" / "x.pdf").is_file()
    r = CliRunner().invoke(main, ["util", "html2pdf", str(tmp_path / "nope.html")])
    assert r.exit_code == 1 and "no such file" in r.output
