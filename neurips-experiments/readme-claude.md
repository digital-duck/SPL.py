### Recipe 1 — `pocketflow-agent` (SPL ID 66) ✓ COMPLETE

**Pattern:** Linear pipeline (chunk → embed → index → retrieve → generate)

**Step 1 — splc describe:**
```bash
cd ~/projects/digital-duck/SPL.py
spl3 splc describe ~/projects/wgong/PocketFlow/cookbook/pocketflow-agent/ \
  --lang "Python — PocketFlow" \
  --adapter claude_cli --model claude-sonnet-4-6

spl3 splc describe ~/projects/digital-duck/SPL.py/neurips-experiments/claude_cli/pocketflow-agent/targets/python_pocketflow/ \
  --lang "Python — PocketFlow" \
  --adapter claude_cli --model claude-sonnet-4-6


```

Spec written to: /home/papagame/projects/digital-duck/SPL.py/neurips-experiments/claude_cli/pocketflow-agent/targets/python_pocketflow/pocketflow-agent-claude_cli-claude-sonnet-4-6-spec.md


```bash
spl3 splc describe ~/projects/digital-duck/SPL.py/neurips-experiments/claude_cli/pocketflow-agent/targets/python_pocketflow/ \
  --lang "Python — PocketFlow" \
  --adapter gemini_cli --model gemini-3-flash-preview
```

**don't use gemini_cli**

  File "/home/papagame/projects/digital-duck/SPL.py/spl/adapters/gemini_cli.py", line 91, in generate
    raise RuntimeError(f"Gemini CLI timed out after {self.timeout}s")
RuntimeError: Gemini CLI timed out after 300s


```bash
spl3 splc describe ~/projects/digital-duck/SPL.py/neurips-experiments/claude_cli/pocketflow-agent/targets/python_pocketflow/ \
  --lang "Python — PocketFlow" \
  --adapter openrouter --model google/gemini-3.1-pro-preview

```

Spec written to: /home/papagame/projects/digital-duck/SPL.py/neurips-experiments/claude_cli/pocketflow-agent/targets/python_pocketflow/pocketflow-agent-openrouter-gemini-31-pro-spec.md



```bash
spl3 splc describe ~/projects/digital-duck/SPL.py/neurips-experiments/claude_cli/pocketflow-agent/targets/python_pocketflow/ \
  --lang "Python — PocketFlow" \
  --adapter ollama --model gemma3

```


Describing 4 file(s) in pocketflow-agent/: flow.py, main.py, nodes.py, utils.py
Spec written to: /home/gong2/projects/wgong/PocketFlow/cookbook/pocketflow-agent/flow-splc-python_pocketflow-spec.md



**Step 2 — text2spl:**
```bash
spl3 text2spl \
  --description ~/projects/wgong/PocketFlow/cookbook/pocketflow-agent/flow-splc-python_pocketflow-spec.md \
  --mode workflow \
  --adapter claude_cli --model claude-sonnet-4-6 \
  -o ~/projects/digital-duck/SPL.py/cookbook-pocketflow/pocketflow-agent/pocketflow-agent-v0.spl
```

Written to /home/gong2/projects/digital-duck/SPL.py/cookbook-pocketflow/pocketflow-agent/pocketflow-agent-v0.spl



**Step 2A — text2mmd:**
```bash
spl3 text2mmd \
  --description ~/projects/wgong/PocketFlow/cookbook/pocketflow-agent/flow-splc-python_pocketflow-spec.md \
  --adapter claude_cli --model claude-sonnet-4-6 \
  --out-dir ~/projects/digital-duck/SPL.py/cookbook-pocketflow/pocketflow-agent/ \
  -o pocketflow-agent.mmd
```

- Markdown (VS Code): /home/gong2/projects/digital-duck/SPL.py/cookbook-pocketflow/pocketflow-agent/pocketflow-agent.md
- HTML (Browser): /home/gong2/projects/digital-duck/SPL.py/cookbook-pocketflow/pocketflow-agent/pocketflow-agent.html
- PNG Image: /home/gong2/projects/digital-duck/SPL.py/cookbook-pocketflow/pocketflow-agent/pocketflow-agent.png


**Step 2B — mmd2spl:**

```bash
spl3 mmd2spl \
  /home/gong2/projects/digital-duck/SPL.py/cookbook-pocketflow/pocketflow-agent/pocketflow-agent.mmd \
  --adapter claude_cli --model claude-sonnet-4-6 \
  -o ~/projects/digital-duck/SPL.py/cookbook-pocketflow/pocketflow-agent/pocketflow-agent.spl
```




**Step 3 — validate:**
```bash
spl3 validate ~/projects/digital-duck/SPL.py/cookbook-pocketflow/pocketflow-agent/pocketflow-agent.spl
```

OK: /home/gong2/projects/digital-duck/SPL.py/cookbook-pocketflow/pocketflow-agent/pocketflow-agent.spl


**Step 3-B - compare**
```bash
spl3 compare /home/gong2/projects/digital-duck/SPL.py/cookbook-pocketflow/pocketflow-agent/pocketflow-agent-v0.spl /home/gong2/projects/digital-duck/SPL.py/cookbook-pocketflow/pocketflow-agent/pocketflow-agent.spl --adapter claude_cli --model claude-opus-4-6
```

Both files implement the same pattern: an agentic research loop that iterates up to 3 times, deciding whether to search or answer at each step. **File 2 is the stronger implementation** — it's more practical, production-ready, and idiomatic, despite being more concise. File 1 is more verbose and pedagogical but relies on simulated searches and has some structural quirks.


**Step 4 — run:**
```bash
spl3 run ~/projects/digital-duck/SPL.py/cookbook-pocketflow/pocketflow-agent/pocketflow-agent.spl \
  --adapter claude_cli --model claude-sonnet-4-6  \
  --param initial_query="What is machine learning?"
```

worked!
LLM calls: 2  Latency: 92064ms
Log:     /home/gong2/.spl/logs/pocketflow_agent-gemini_cli-20260430-012041.md


**Step 5 — splc compile:**
```bash
spl3 splc compile ~/projects/digital-duck/SPL.py/cookbook-pocketflow/pocketflow-agent/pocketflow-agent.spl \
  --lang python/pocketflow
```

used self_refine pattern, should be reAct pattern

```bash
spl3 splc compile ~/projects/digital-duck/SPL.py/cookbook-pocketflow/pocketflow-agent/pocketflow-agent.spl \
  --lang python/pocketflow \
  --llm \
  --adapter claude_cli --model claude-sonnet-4-6 --overwrite

```


Written: /home/gong2/projects/digital-duck/SPL.py/cookbook-pocketflow/pocketflow-agent/targets/python_pocketflow/pocketflow-agent_python_pocketflow.py
Written: /home/gong2/projects/digital-duck/SPL.py/cookbook-pocketflow/pocketflow-agent/targets/python_pocketflow/readme.md
Written: /home/gong2/projects/digital-duck/SPL.py/cookbook-pocketflow/pocketflow-agent/targets/python_pocketflow/splc_manifest.json


**Step 6 — python run:**
```bash
python /home/gong2/projects/digital-duck/SPL.py/cookbook-pocketflow/pocketflow-agent/targets/python_pocketflow/pocketflow-agent_python_pocketflow.py \
  --initial-query "What is machine learning?" 
```


