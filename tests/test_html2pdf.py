"""spl3 util html2pdf: browser lookup, the command it builds, and the CLI, with a fake browser (no Chromium needed)."""
import stat
from pathlib import Path

import pytest
from click.testing import CliRunner

from spl3 import html2pdf
from spl3.cli import main

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


def test_command_prints_the_page_without_header_and_footer(tmp_path):
    cmd = html2pdf._command("chromium", tmp_path / "o.pdf", tmp_path / "d.html")
    assert "--headless" in cmd and "--no-pdf-header-footer" in cmd
    assert cmd[-1].startswith("file://") and cmd[-1].endswith("d.html")
    assert f"--print-to-pdf={tmp_path / 'o.pdf'}" in cmd


def test_missing_browser_is_an_error(monkeypatch):
    monkeypatch.delenv("CHROME", raising=False)
    monkeypatch.setattr(html2pdf.shutil, "which", lambda name: None)
    with pytest.raises(html2pdf.Html2PdfError, match="no Chromium"):
        html2pdf.find_browser()


def test_html_to_pdf_writes_next_to_the_input_by_default(tmp_path, fake_browser):
    deck = tmp_path / "deck.html"
    deck.write_text("<html></html>")
    out = html2pdf.html_to_pdf(deck)
    assert out == tmp_path / "deck.pdf" and out.read_bytes().startswith(b"%PDF")
    assert html2pdf.count_pages(out) == 2          # /Type /Pages is not a page


def test_cli_output_option_and_missing_input(tmp_path, fake_browser):
    deck = tmp_path / "deck.html"
    deck.write_text("<html></html>")
    r = CliRunner().invoke(main, ["util", "html2pdf", str(deck), "-o", str(tmp_path / "sub" / "x.pdf")])
    assert r.exit_code == 0 and "2 pages" in r.output and (tmp_path / "sub" / "x.pdf").is_file()
    r = CliRunner().invoke(main, ["util", "html2pdf", str(tmp_path / "nope.html")])
    assert r.exit_code == 1 and "no such file" in r.output
