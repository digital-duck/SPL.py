"""A-2 tests — SageMath in the domain-notebook targets.

Covers (see docs/DEV/sage_lean_integration_plan.md §A.2–A.3):
  - `DomainConfig.kernel_name` → emitted `.ipynb` kernelspec metadata
    (the artifact carries its runtime — DODA)
  - `graph_lib.verify_content` engine dispatch: `verifier: "sage"` and the
    `"sage|sympy"` fallback-tiering policy, with engine-of-record in the
    return value
"""

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cookbook" / "74_domain_textbook"))

import graph_lib  # noqa: E402
from spl.lexer import Lexer  # noqa: E402
from spl3.parser import SPL3Parser  # noqa: E402
from spl3.splc.transpiler_linalg import LinalgTranspiler  # noqa: E402
from spl3.splc.transpiler_domain_textbook import DomainTextbookTranspiler  # noqa: E402

_MINIMAL_SPL = """\
WORKFLOW test_workflow
    OUTPUT: @result TEXT
DO
    SOLVE @result TEXT := str(2 + 2)
    RETURN @result
END
"""


def _sage_available() -> bool:
    try:
        import sage.all  # noqa: F401
        return True
    except Exception:
        return False


def _transpile(transpiler_cls, kernel_name=None) -> dict:
    tokens = Lexer(_MINIMAL_SPL).tokenize()
    program = SPL3Parser(tokens).parse()
    transpiler = transpiler_cls("test_workflow", kernel_name=kernel_name)
    return json.loads(transpiler.transpile(program))


class TestKernelspecEmission:
    def test_default_kernelspec_is_python3(self):
        nb = _transpile(LinalgTranspiler)
        ks = nb["metadata"]["kernelspec"]
        assert ks["name"] == "python3"
        assert ks["language"] == "python"
        assert nb["metadata"]["splc"]["kernel_name"] == "python3"

    def test_sagemath_kernelspec_emitted(self):
        nb = _transpile(LinalgTranspiler, kernel_name="sagemath")
        ks = nb["metadata"]["kernelspec"]
        assert ks == {"display_name": "SageMath", "language": "sage", "name": "sagemath"}
        assert nb["metadata"]["splc"]["kernel_name"] == "sagemath"

    def test_sagemath_kernelspec_domain_textbook(self):
        nb = _transpile(DomainTextbookTranspiler, kernel_name="sagemath")
        assert nb["metadata"]["kernelspec"]["name"] == "sagemath"

    def test_unknown_kernel_name_falls_back_to_name_as_display(self):
        nb = _transpile(LinalgTranspiler, kernel_name="julia-1.10")
        ks = nb["metadata"]["kernelspec"]
        assert ks["name"] == "julia-1.10"
        assert ks["display_name"] == "julia-1.10"

    def test_cells_unchanged_by_kernel_name_except_kernel_check(self):
        # A non-default kernel adds exactly one thing: the kernel-check banner
        # appended to the setup cell (A-3). All other cells are identical.
        default = _transpile(LinalgTranspiler)
        sage = _transpile(LinalgTranspiler, kernel_name="sagemath")
        assert default["cells"][0] == sage["cells"][0]      # title cell
        assert default["cells"][2:] == sage["cells"][2:]    # body cells
        default_setup = "".join(default["cells"][1]["source"])
        sage_setup = "".join(sage["cells"][1]["source"])
        assert sage_setup.startswith(default_setup)
        assert "Kernel check" in sage_setup[len(default_setup):]


class TestVerifyContentDispatch:
    DOMAIN = {"domain": "linalg"}

    def test_domain_default_unchanged(self):
        # No verifier arg → pre-A-2 behavior, plain "pass"
        assert graph_lib.verify_content("section text", self.DOMAIN) == "pass"

    def test_explicit_sympy_engine_records_engine(self):
        out = graph_lib.verify_content("section text", self.DOMAIN, verifier="sympy")
        assert out == "pass (sympy)"

    def test_unknown_engine_fails(self):
        out = graph_lib.verify_content("section text", self.DOMAIN,
                                       verifier="no_such_engine_xyz")
        assert out.startswith("fail:")

    def test_fallback_tier_prefers_first_available(self):
        # "sage|sympy": sage when installed, else sympy — never a hard fail
        out = graph_lib.verify_content("section text", self.DOMAIN, verifier="sage|sympy")
        expected = "pass (sage)" if _sage_available() else "pass (sympy)"
        assert out == expected

    @pytest.mark.skipif(not _sage_available(), reason="SageMath not installed")
    def test_sage_engine(self):
        out = graph_lib.verify_content("section text", self.DOMAIN, verifier="sage")
        assert out == "pass (sage)"


class TestEngineOfRecordInCache:
    """A-3: the verifier engine-of-record rides in cache provenance."""

    @pytest.fixture
    def cache(self, tmp_path):
        from dd_cache import InMemoryCache
        from spl3.cache.content import ContentCache
        return ContentCache(store=InMemoryCache(),
                            meta_path=str(tmp_path / "meta.db"))

    def test_put_records_verifier(self, cache):
        entry = cache.put(
            concept="eigenpair", content="A v = lambda v",
            provenance="machine_verified", params={}, rubric_version="v1",
            dep_hashes={}, verifier="sage",
        )
        assert entry.verifier == "sage"

    def test_get_returns_verifier(self, cache):
        cache.put(concept="eigenpair", content="A v = lambda v",
                  provenance="machine_verified", params={}, rubric_version="v1",
                  dep_hashes={}, verifier="sage")
        got = cache.get(concept="eigenpair", params={}, rubric_version="v1",
                        dep_hashes={}, min_provenance="machine_verified")
        assert got is not None
        assert got.verifier == "sage"

    def test_default_is_unverified(self, cache):
        entry = cache.put(
            concept="span", content="...", provenance="machine_generated",
            params={}, rubric_version="v1", dep_hashes={},
        )
        assert entry.verifier == ""

    def test_migration_adds_column_to_old_db(self, tmp_path):
        # Simulate a DB created before A-3 (no verifier column), then reopen.
        import sqlite3
        from spl3.cache.meta import MetaStore
        db = tmp_path / "old_meta.db"
        conn = sqlite3.connect(db)
        conn.executescript("""
            CREATE TABLE content_meta (
                key TEXT PRIMARY KEY, concept TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                provenance TEXT NOT NULL DEFAULT 'machine_generated',
                rubric_ver TEXT NOT NULL, dep_hashes TEXT NOT NULL,
                params TEXT NOT NULL, adapter TEXT, model TEXT,
                token_cost INTEGER DEFAULT 0, hit_count INTEGER DEFAULT 0,
                stale INTEGER DEFAULT 0, verdict TEXT,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            INSERT INTO content_meta VALUES
                ('k1','c1','h1','machine_generated','v1','{}','{}','','',0,0,0,NULL,'t','t');
        """)
        conn.commit()
        conn.close()

        meta = MetaStore(meta_path=str(db))
        row = meta.get_meta("k1")
        assert row is not None
        assert (row["verifier"] or "") == ""  # old rows default to unverified
        # And new writes can record an engine
        meta.put(key="k2", concept="c2", content_hash="h2",
                 provenance="machine_verified", rubric_version="v1",
                 dep_hashes={}, params={}, adapter="", model="",
                 token_cost=0, verifier="sympy")
        assert meta.get_meta("k2")["verifier"] == "sympy"


class TestKernelCheckBanner:
    """A-3: runtime downgrade notice in notebooks compiled for a non-default kernel."""

    def test_sagemath_notebook_has_kernel_check(self):
        nb = _transpile(LinalgTranspiler, kernel_name="sagemath")
        setup_src = "".join(nb["cells"][1]["source"])
        assert "compiled for the 'sagemath' kernel" in setup_src
        assert "fall back to sympy" in setup_src

    def test_python3_notebook_has_no_kernel_check(self):
        nb = _transpile(LinalgTranspiler)
        setup_src = "".join(nb["cells"][1]["source"])
        assert "compiled for the" not in setup_src

    def test_emitted_cache_put_accepts_verifier(self):
        nb = _transpile(LinalgTranspiler)
        setup_src = "".join(nb["cells"][1]["source"])
        assert 'verifier: str = ""' in setup_src
        assert "verifier=verifier," in setup_src
