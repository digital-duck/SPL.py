"""text2SPL Knowledge Studio — landing page.

Run with:
    streamlit run spl/ui/streamlit/SPL_UI.py
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
import db
import code_rag_bridge as rag
import spl3_rag_bridge as spl3_rag

db.init_db()

st.set_page_config(page_title="text2SPL Studio", layout="wide")

# ── Page navigation via ?page= query param (set by `spl3 ui --page N`) ────────
_PAGE_MAP = {
    "0": "0_🗺️_Text2Mermaid",  "text2mermaid": "0_🗺️_Text2Mermaid",
    "1": "1_⚡_Text2SPL",       "text2spl": "1_⚡_Text2SPL",
    "2": "2_📚_Review",          "review": "2_📚_Review",
    "3": "3_🔍_Code_RAG",        "code_rag": "3_🔍_Code_RAG",
    "4": "4_🔧_SPLc",            "splc": "4_🔧_SPLc",
    "5": "5_📄_Target_Review",   "target_review": "5_📄_Target_Review",
    "6": "6_🧪_NeurIPS_Lab",     "neurips": "6_🧪_NeurIPS_Lab",
    "7": "7_📊_Ablation_Results","ablation": "7_📊_Ablation_Results",
    "8": "8_🔍_RT_Inspect",      "rt_inspect": "8_🔍_RT_Inspect",
    "9": "9_🔬_Compare",         "compare": "9_🔬_Compare",
}
_qp = st.query_params.get("page", "")
if _qp:
    _target = _PAGE_MAP.get(str(_qp).lower())
    if _target:
        st.sidebar.info(f"💡 Tip: click **{_target}** in the sidebar to go directly to that page.")

st.title("text2SPL Knowledge Studio")
st.caption("Natural language → SPL 2.0 · Interactive compiler + knowledge accumulator")

st.markdown("""
Use the sidebar to navigate:

| Page | What it does |
|---|---|
| **Text-to-SPL** | Enter a description, compile to SPL, inspect the code, and run it |
| **Review** | Browse all generated scripts and their execution history |
| **Code-RAG** | Manage the retrieval store that improves future compilations |
| **SPLc** | Compile a `.spl` logical view into Go / Python / LangGraph / CrewAI / AutoGen |
| **Target Review** | Browse all compiled target-language artifacts and manifests |

Every compile and every run is saved to a local SQLite database
(`data/knowledge.db`). The Code-RAG store (ChromaDB) indexes validated
(description → SPL) pairs so the compiler can retrieve semantically similar
examples at compile time — the more pairs indexed, the better the output.

`splc` implements the **DODA** (Design Once, Deploy Anywhere) principle:
the `.spl` file is the invariant logical view; `splc` produces
hardware/framework-specific physical artifacts on demand.
""")

st.divider()

scripts    = db.get_scripts()
executions = db.get_all_executions()
success    = sum(1 for e in executions if e["return_code"] == 0)
n_rag      = rag.count() if rag.is_available() else -1

n_spl3 = spl3_rag.count() if spl3_rag.is_available() else -1

diagrams_dir = Path(__file__).parent / "data" / "diagrams"
n_diagrams = len(list(diagrams_dir.glob("*.mmd"))) if diagrams_dir.exists() else 0

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Diagrams approved",    n_diagrams, help="Mermaid diagrams approved via Text2Mermaid")
col2.metric("Scripts generated",    len(scripts))
col3.metric("Executions recorded",  len(executions))
col4.metric("Successful runs",      success)

if n_rag >= 0:
    col5.metric("Code-RAG pairs",   n_rag)
else:
    col5.metric("Code-RAG pairs",   "n/a", help="chromadb not installed")

if n_spl3 >= 0:
    col6.metric("SPL3 Cookbook",    n_spl3, help="Recipes in SPL3 RAG store")
else:
    col6.metric("SPL3 Cookbook",    "n/a", help="Run index_recipes.py to populate")
