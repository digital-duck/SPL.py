# SPL Setup Guide — Fresh Ubuntu Machine

Everything needed to run the full SPL stack — core CLI, the cookbook, and the
complete verifier ladder (SymPy → SageMath → Lean 4 + mathlib) — starting from
a clean Ubuntu install. Written against Ubuntu 22.04/24.04; ladder verified
end-to-end on the original dev machine 2026-06-11. The `/opt/lean` relocatable
layout (§6) was added 2026-06-12 for machines that keep big toolchains on a
dedicated HDD mount.

**What `pyproject.toml` covers, and what it cannot:**

| Layer | Covered by `pip install`? |
|---|---|
| SPL core (`spl3` CLI, dd-* ecosystem, Anthropic SDK) | ✅ base dependencies |
| IPython kernel mode (`--kernel`) | ✅ `[kernel]` extra |
| SageMath (passagemath wheels) | ✅ `[sage]` extra — but the **kernelspec registration** (§5) is a manual post-step |
| SymPy / NetworkX (cookbook recipes 67/71/74/77) | ❌ not declared — install explicitly (§3) |
| Lean 4 toolchain (elan), the pinned REPL, mathlib | ❌ entirely outside pip — `setup_lean.sh` (§6) |
| LLM adapter auth (Claude Code OAuth, Ollama models) | ❌ per-machine (§4) |
| conda env / Python 3.11 | ❌ per-machine (§2) |

Sections are ordered so each one's verification step can run before moving on.

---

## 1. System packages

```bash
sudo apt update
sudo apt install -y git curl ca-certificates build-essential
```

`git` and `curl` are hard requirements (elan installer, repl clone, mathlib
cache). `build-essential` is belt-and-braces for `lake build` — the Lean
toolchain is largely self-contained, but a system linker avoids surprises.

**Disk budget** (plan ~15 GB free for the full ladder):

| Component | Size | Location (recommended) |
|---|---|---|
| conda env `spl123` (incl. passagemath wheels ~1.3 GB) | ~4 GB | conda's env dir (`/home`, HDD) |
| `/opt/lean/elan` (Lean toolchains, `ELAN_HOME`) | ~2.7 GB | `/opt` (HDD) |
| `/opt/lean/repl` (pinned REPL build, `SPL_LEAN_REPL_DIR`) | ~0.2 GB | `/opt` (HDD) |
| `/opt/lean/spl_lean` + mathlib olean cache (`SPL_LEAN_PROJECT_DIR`) | ~7.4 GB | `/opt` (HDD) |

> **Storage note:** keep the big, infrequently-updated pieces off the SSD.
> SageMath is **not a standalone app** here — it's passagemath pip wheels
> inside the conda env, so it lives wherever the env lives (the conda
> default under `/home` is fine when `/home` is on the HDD). The Lean stack
> (~10 GB total) is fully relocatable: §6 directs all of it to `/opt/lean`
> via three environment variables that both `setup_lean.sh` (install time)
> and `spl3/lean_bridge.py` (run time) honor. Leaving the variables unset
> keeps the legacy layout (`~/.elan` + in-repo `cookbook/tools/lean/`) —
> both layouts are supported.

---

## 2. Conda + the `spl123` environment

Install Miniconda (skip if conda is already present):

```bash
curl -fsSLo /tmp/miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
# Install to ~/miniconda3 — lands on HDD when /home is on a spinning disk
# (the passagemath wheels ~1.3 GB live inside the env, so they follow it).
# Avoid an SSD path for the conda root.
bash /tmp/miniconda.sh -b -p "$HOME/miniconda3"
"$HOME/miniconda3/bin/conda" init bash
exec bash   # reload the shell so `conda` is on PATH
```

Create the env (the repo targets Python ≥ 3.11; the dev machine runs 3.11):

```bash
conda create -n spl123 python=3.11 -y
conda activate spl123
```

> **Convention used everywhere in this repo:** `conda activate spl123` first,
> then call `spl3` plainly — never by absolute path.

---

## 3. SPL itself (editable install + cookbook extras)

```bash
git clone https://github.com/digital-duck/SPL.py.git ~/projects/digital-duck/SPL.py
cd ~/projects/digital-duck/SPL.py

pip install -e ".[kernel,sage,dev]"

# Cookbook prerequisites NOT declared in pyproject.toml:
#   sympy    — recipes 67/71/77 (the SymPy rung) and the concept-book verifiers
#   networkx — recipes 71/74 (domain concept graphs)
pip install sympy networkx
```

Extras explained:

- `kernel` — IPython/Jupyter client, required for `spl3 run --kernel`
  (the Lean bridge keeps its REPL state in the persistent kernel session).
- `sage` — SageMath as **passagemath wheels**: resolves wheels-only, no source
  build, and — the key property — runs in the *same* interpreter as the env
  (a conda-forge or distro Sage would reintroduce a separate-Python gap).
- `dev` — pytest + the vector/embedding backends the test suite exercises.
- `ui` (optional, not needed for the verifier ladder) — Streamlit apps
  (`cookbook/67_symbolic_math/app*.py`).

**Verify:**

```bash
spl3 --help                          # CLI resolves
python -c "import sympy, networkx, sage.all; print('stack ok')"
```

---

## 4. LLM adapters

At least one adapter is needed to run workflows. The cookbook harnesses
default to `claude_cli` (model id `m001`); the experiment rosters also use
local Ollama models.

### 4a. `claude_cli` (recommended first)

Install Claude Code and authenticate (OAuth, subscription flat-rate):

```bash
curl -fsSL https://claude.ai/install.sh | bash    # or: npm install -g @anthropic-ai/claude-code
claude --version
claude          # then run /login once, interactively
```

### 4b. `ollama` (local models — experiment Axis 2)

```bash
curl -fsSL https://ollama.com/install.sh | sh
# Pull only what you plan to benchmark; the recipe-77 roster (m002–m010):
ollama pull gemma3
ollama pull phi4
ollama pull qwen2.5
ollama pull deepseek-r1
ollama pull rnj-1        # Essential AI 8B STEM model (m010)
# ... see run_experiment.py --list for the full roster
```

### 4c. API-key adapters (optional)

`openrouter` / `anthropic` adapters read keys from the environment
(`OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`). Not required if 4a or 4b is set up.

**Verify** (one LLM call):

```bash
spl3 run cookbook/05_self_refine/self_refine.spl --llm claude_cli
```

---

## 5. SageMath rung (recipe 75, recipe 77 `backend=sage`)

The wheels are already in from §3. Two distinct integration routes share them:

1. **In-process TOOL_API route** (recipe 77's `solve_step_with_sage`) —
   nothing more to set up; `from sage.all import ...` just works.
2. **Kernel route** (`spl3 run --kernel-name sagemath`, recipe 75) — register
   the Jupyter kernelspec once:

```bash
python -m sage.repl.ipython_kernel.install --user
jupyter kernelspec list        # must show: sagemath
```

**Verify:**

```bash
python -c "from sage.all import QQ; print(QQ['x']('x^5-x-1').galois_group())"
# → Transitive group number 5 of degree 5
spl3 run cookbook/75_sage_math/basic_sagemath.spl --kernel-name sagemath --llm claude_cli
```

---

## 6. Lean 4 + mathlib rung (recipes 76, 71 `lean_payoffs`, 77 `backend=lean`)

One idempotent script provisions everything, pinned to `v4.30.0`
(the pin must match `REPL_REVISION` in `spl3/lean_bridge.py` — the script
and the bridge are kept in sync in-repo):

> **macOS note:** macOS does not create a group named after your username
> (unlike Linux). Use `$(id -gn)` for the group — it resolves to your
> primary group (typically `staff`). The command below already does this.
> Also substitute `~/.zshrc` for `~/.bashrc` if your shell is zsh
> (the macOS default since Catalina).

```bash
# One-time: create a user-owned home for the Lean stack on the big HDD.
# (/opt is root-owned; this is the only sudo in the whole Lean setup.)
sudo install -d -o "$USER" -g "$(id -gn)" /opt/lean

# Direct the entire Lean stack (~10 GB) to /opt/lean. These three variables
# are read by setup_lean.sh at INSTALL time and by spl3/lean_bridge.py at
# RUN time, so they must be set in every shell — persist them in ~/.bashrc
# (Linux) :
cat >> ~/.bashrc <<'EOF'
export ELAN_HOME=/opt/lean/elan
export PATH="$ELAN_HOME/bin:$PATH"
export SPL_LEAN_REPL_DIR=/opt/lean/repl
export SPL_LEAN_PROJECT_DIR=/opt/lean/spl_lean
EOF
source ~/.bashrc

# (macOS)
cat >> ~/.zshrc <<'EOF'
export ELAN_HOME=/opt/lean/elan
export SPL_LEAN_REPL_DIR=/opt/lean/repl
export SPL_LEAN_PROJECT_DIR=/opt/lean/spl_lean
EOF
source ~/.zshrc
# (Skip this block entirely to use the legacy layout: ~/.elan plus
#  in-repo cookbook/tools/lean/ — fine when /home is on the HDD.)

# Stage 1 — elan + pinned leanprover-community/repl + spl_lean lake project.
# First run downloads a Lean toolchain (~2.7 GB into $ELAN_HOME) and builds
# the REPL; allow 10–20 minutes. Stage 1 is stdlib-only — no mathlib yet.
bash cookbook/tools/lean/setup_lean.sh

# Stage 2 — mathlib (needed by recipes 71/77; recipe 76 runs stdlib-only).
# Downloads the prebuilt olean cache (~5 GB, `lake exe cache get`) — mathlib
# is NEVER compiled from source. Allow 15–30 minutes on a fast connection.
bash cookbook/tools/lean/setup_lean.sh --with-mathlib
```

Network notes:

- The script needs outbound HTTPS to `elan.lean-lang.org`, `github.com`,
  and mathlib's cache CDN.
- The B-5 citation fallback queries `loogle.lean-lang.org` at run time;
  if that host is unreachable the bridge degrades gracefully to local
  `exact?` search (the network is a search hint, never a trust source —
  every candidate is kernel-checked locally).

**Verify:**

```bash
python -c "from spl3.lean_bridge import repl_available, mathlib_available; print(repl_available(), mathlib_available())"
# → True True

# Stdlib tier (fast, ~5 s warm-up):
spl3 run cookbook/76_lean_proof/lean_proof.spl --kernel --llm ollama:gemma3  # claude_cli

# Mathlib tier (first warm-up imports mathlib, 10–40 s):
spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel \
  --llm ollama:gemma3 \
  --param backend=lean --param problem="the square of any real number is nonnegative"
  # --llm claude_cli \
# → Badge: machine_proved (citation path, e.g. sq_nonneg)
```

---

## 7. Full verification checklist

Run top to bottom on the new machine; each line states its expected outcome.

```bash
conda activate spl123
cd ~/projects/digital-duck/SPL.py

# 1. Test suite — Lean/Sage-dependent tests skip cleanly when a rung is
#    missing, so this is safe to run at any point after §3.
#    With everything provisioned (2026-06-11): 888 passed, 8 skipped.
python -m pytest tests/ -q

# 2. Kernel + bridge probes
python -c "from spl3.lean_bridge import repl_available, mathlib_available; print(repl_available(), mathlib_available())"
jupyter kernelspec list | grep sagemath

# 3. One smoke run per verifier rung (recipe 77 covers all three):
python cookbook/77_neurosymbolic/run_experiment.py -m m001 -p p003 -s true --backend sympy   # ✓ complete
python cookbook/77_neurosymbolic/run_experiment.py -m m001 -p p021 -s true                   # ✓ complete (Galois → S5)
python cookbook/77_neurosymbolic/run_experiment.py -m m001 -p p025 -s true                   # ✓ machine_proved (Nat.add_comm)
```

If all three smoke cells pass, the entire ladder — SymPy instance checks,
Sage/PARI exact computation, and Lean kernel-checked proof against mathlib —
is live on the machine.

---

## 8. Known gotchas

- **`spl3: command not found`** — the env isn't activated; `conda activate
  spl123` first (never call the binary by absolute path).
- **macOS: `install: unknown group <username>`** — macOS does not auto-create
  a group named after your username. Replace `-g "$USER"` with `-g "$(id -gn)"`
  (resolves to your primary group, usually `staff`):
  `sudo install -d -o "$USER" -g "$(id -gn)" /opt/lean`
- **`lake build` is slow the first time** — it is downloading a toolchain;
  subsequent runs of `setup_lean.sh` are near-instant (idempotent).
- **`lake: command not found`** — `$ELAN_HOME/bin` is not on PATH in that
  shell. Fix: `export PATH="/opt/lean/elan/bin:$PATH"` for the session, or
  add `export PATH="$ELAN_HOME/bin:$PATH"` to `~/.zshrc` / `~/.bashrc`
  (after the `ELAN_HOME` export) and reload.
- **Lean smoke run fails with "repl not found"** — the error message itself
  carries the setup command; it means §6 stage 1 hasn't run on this machine.
- **Lean works in one shell but not another (after the `/opt/lean` layout)** —
  the three `ELAN_HOME` / `SPL_LEAN_*` variables aren't exported in that
  shell; they must come from `~/.bashrc` (§6), not a one-off `export`. The
  bridge falls back to `~/.elan` + in-repo paths when they're unset.
- **Sage kernel missing under `--kernel-name sagemath`** — `spl3 run` fails
  fast with the registration command (§5); the in-process route (recipe 77)
  works without it.
- **mathlib cache download times out** — `lake exe cache get` downloads ~8459
  files from Azure CDN and can time out on a few of them. The script now
  retries automatically (up to 3×). If it still fails, re-run manually:
  `cd /opt/lean/spl_lean && lake exe cache get && lake build` — already-
  downloaded files are kept; only the missing ones are fetched.
- **mathlib warm-up per process** — the first Lean check in a run pays the
  mathlib import (10–40 s); every later check in the same run branches off
  the warm environment.
- **conda-forge Sage** — don't. It ships its own Python and breaks the
  same-interpreter property the integration relies on; the `[sage]` pip
  extra (passagemath) is the supported route.
