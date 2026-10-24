"""spl3 logging: one `spl` logger tree on dd-logging; `spl3 run` writes a .log/.jsonl next to the run report."""
import json
import logging
from pathlib import Path

import pytest
from click.testing import CliRunner

from spl3.logging_config import ROOT, disable_logging, get_logger, setup_logging

pytestmark = pytest.mark.filterwarnings("ignore")


@pytest.fixture(autouse=True)
def _reset():
    yield
    disable_logging()
    logging.getLogger(ROOT).propagate = True      # other tests rely on caplog seeing `spl.*`


def test_all_spl3_modules_log_under_spl():
    import spl3.executor, spl3.registry, spl3._loader, spl3.composer
    for mod, name in [(spl3.executor, "executor"), (spl3.registry, "registry"), (spl3._loader, "loader"),
                      (spl3.composer, "composer")]:
        assert mod._log.name == f"spl.{name}"


def test_no_stray_getlogger_calls():
    offenders = [str(p) for p in Path("spl3").rglob("*.py")
                 if p.name != "logging_config.py" and "getLogger" in p.read_text(encoding="utf-8")]
    assert offenders == []


def test_jsonl_file_via_setup_logging(tmp_path):
    path = setup_logging("t", log_dir=tmp_path, log_format="jsonl")
    get_logger("executor").info("hello")
    for h in logging.getLogger(ROOT).handlers:
        h.flush()
    row = json.loads(path.read_text().splitlines()[0])
    assert row["logger"] == "spl.executor" and row["msg"] == "hello"


def _cli():
    pytest.importorskip("dd_cache", reason="spl3.cli imports the dd-cache extra")
    from spl3.cli import main
    return main


def test_run_writes_log_and_jsonl_trace(tmp_path):
    main = _cli()
    spl = tmp_path / "hello.spl"
    spl.write_text('WORKFLOW hello\n  INPUT: @name TEXT DEFAULT \'x\'\n  OUTPUT: @r TEXT\nDO\n'
                   '  @r := \'done\'\n  COMMIT @r\nEND\n')
    result = CliRunner().invoke(main, ["run", str(spl), "--adapter", "echo", "--persistence", "none",
                                       "--param", f"log_dir={tmp_path}/logs", "--log-format", "both"])
    assert result.exit_code == 0, (result.output, result.exception)
    logs = list((tmp_path / "logs").glob("hello-*"))
    assert {p.suffix for p in logs} >= {".log", ".jsonl"}, result.output
    events = [json.loads(l).get("event") for l in next(p for p in logs if p.suffix == ".jsonl").read_text().splitlines()]
    assert "workflow.start" in events and "workflow.end" in events


def test_no_log_flag_writes_no_log_file(tmp_path):
    main = _cli()
    spl = tmp_path / "hello.spl"
    spl.write_text('WORKFLOW hello\n  INPUT: @name TEXT DEFAULT \'x\'\n  OUTPUT: @r TEXT\nDO\n'
                   '  @r := \'done\'\n  COMMIT @r\nEND\n')
    CliRunner().invoke(main, ["run", str(spl), "--adapter", "echo", "--persistence", "none",
                              "--param", f"log_dir={tmp_path}/logs", "--no-log"])
    assert not list((tmp_path / "logs").glob("*.log")) and not list((tmp_path / "logs").glob("*.jsonl"))
