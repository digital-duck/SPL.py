"""SPL's logging: the `spl` logger tree on top of dd-logging.

    from spl3.logging_config import get_logger
    _log = get_logger("executor")            # -> spl.executor

Every spl3 module logs under the single root `spl`. The CLI calls `setup_console_logging` at start
(warnings to stderr, as before) and `setup_logging` for `spl3 run` (a timestamped .log and/or .jsonl in
the run's log directory). Used as a library, nothing is configured and nothing is printed.
"""
from __future__ import annotations

from pathlib import Path

from dd_logging import ProjectLogging

ROOT = "spl"
LOG_DIR = Path.home() / ".spl" / "logs"

_pl = ProjectLogging(ROOT, log_dir=LOG_DIR)

get_logger = _pl.get_logger
setup_logging = _pl.setup_logging
setup_console_logging = _pl.setup_console_logging
disable_logging = _pl.disable_logging
log_event = _pl.log_event
