# PocketFlow SPL Round-Trip Experiments: Gemini CLI Adapter

**Purpose**: Comprehensive validation of the Visual Workflow Programming pipeline using `gemini_cli` adapter to complete the 6×3 adapter comparison matrix for the NeurIPS 2026 paper.

**Parallel Experiments**: 
- Claude CLI results: `/SPL.py/cookbook-pocketflow/` (complete)
- **Gemini CLI results**: `/SPL.py/cookbook-pocketflow-gemini/` (this folder)
- Ollama results: Part of main claude experiment comparisons

## Experimental Setup

```bash
cd ~/projects/digital-duck/SPL.py

# Environment verification
conda activate base
pip list | grep spl  # Should show spl-llm and editable SPL installation
spl3 show --adapter gemini_cli --model  # Verify gemini_cli availability
```

**Expected Gemini Models:**
- gemini-2.5-flash
- gemini-2.5-flash-lite  
- gemini-3-flash-preview
- gemini-3.1-flash-lite-preview

## Recipe Experiments

### Recipe 1: pocketflow-agent (ReAct Pattern)

**Oracle**: `~/projects/digital-duck/PocketFlow/cookbook/pocketflow-agent/`

```bash
# Step 1: Extract specification from PocketFlow oracle
spl3 splc describe ~/projects/digital-duck/PocketFlow/cookbook/pocketflow-agent/ \
  --lang "Python — PocketFlow" --adapter gemini_cli \
  -o ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-agent/

# Step 2: Generate SPL from specification  
spl3 text2spl \
  --description ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-agent/flow-splc-python_pocketflow-spec.md \
  --mode workflow --adapter gemini_cli \
  -o ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-agent/pocketflow-agent.spl

# Step 3: Validate SPL syntax
spl3 validate ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-agent/pocketflow-agent.spl

# Step 4: Test SPL execution
spl3 run ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-agent/pocketflow-agent.spl \
  --adapter gemini_cli \
  --param question="Who is Alan Turing?" \
  --param max_iterations=2

# Step 5: Compile to target runtime
spl3 splc compile ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-agent/pocketflow-agent.spl \
  --lang python/pocketflow \
  --out-dir ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-agent/targets/

# Step 6: Test compiled Python implementation
python ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-agent/targets/python_pocketflow/pocketflow-agent_python_pocketflow.py \
  --question "Who is Alan Turing?" --max_iterations 2
```

### Recipe 2: pocketflow-rag (Linear Pipeline)

**Oracle**: `~/projects/digital-duck/PocketFlow/cookbook/pocketflow-rag/`

```bash
# Step 1: Extract specification  
spl3 splc describe ~/projects/digital-duck/PocketFlow/cookbook/pocketflow-rag/ \
  --lang "Python — PocketFlow" --adapter gemini_cli \
  -o ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-rag/

# Step 2: Generate SPL
spl3 text2spl \
  --description ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-rag/flow-splc-python_pocketflow-spec.md \
  --mode workflow --adapter gemini_cli \
  -o ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-rag/pocketflow-rag.spl

# Step 3: Validate SPL
spl3 validate ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-rag/pocketflow-rag.spl

# Step 4: Test SPL execution
spl3 run ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-rag/pocketflow-rag.spl \
  --adapter gemini_cli --param question="What is machine learning?"

# Step 5: Compile to target runtime
spl3 splc compile ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-rag/pocketflow-rag.spl \
  --lang python/pocketflow \
  --out-dir ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-rag/targets/

# Step 6: Test compiled implementation  
python ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-rag/targets/python_pocketflow/pocketflow-rag_python_pocketflow.py \
  --question "What is machine learning?"
```

### Recipe 3: pocketflow-judge (Linear + Evaluation)

**Oracle**: `~/projects/digital-duck/PocketFlow/cookbook/pocketflow-judge/`

```bash
# Step 1: Extract specification
spl3 splc describe ~/projects/digital-duck/PocketFlow/cookbook/pocketflow-judge/ \
  --lang "Python — PocketFlow" --adapter gemini_cli \
  -o ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-judge/

# Step 2: Generate SPL  
spl3 text2spl \
  --description ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-judge/flow-splc-python_pocketflow-spec.md \
  --mode workflow --adapter gemini_cli \
  -o ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-judge/pocketflow-judge.spl

# Step 3: Validate SPL
spl3 validate ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-judge/pocketflow-judge.spl

# Step 4: Test SPL execution
spl3 run ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-judge/pocketflow-judge.spl \
  --adapter gemini_cli \
  --param candidate_a="Rayleigh scattering explains why the sky is blue." \
  --param candidate_b="The sky is blue because water reflects into it."

# Step 5: Compile to target runtime
spl3 splc compile ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-judge/pocketflow-judge.spl \
  --lang python/pocketflow \
  --out-dir ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-judge/targets/

# Step 6: Test compiled implementation
python ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-judge/targets/python_pocketflow/pocketflow-judge_python_pocketflow.py \
  --candidate_a "Rayleigh scattering explains why the sky is blue." \
  --candidate_b "The sky is blue because water reflects into it."
```

### Recipe 4: pocketflow-thinking (Self-Refine)

**Oracle**: `~/projects/digital-duck/PocketFlow/cookbook/pocketflow-thinking/`

```bash
# Step 1: Extract specification
spl3 splc describe ~/projects/digital-duck/PocketFlow/cookbook/pocketflow-thinking/ \
  --lang "Python — PocketFlow" --adapter gemini_cli \
  -o ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-thinking/

# Step 2: Generate SPL
spl3 text2spl \
  --description ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-thinking/flow-splc-python_pocketflow-spec.md \
  --mode workflow --adapter gemini_cli \
  -o ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-thinking/pocketflow-thinking.spl

# Step 3: Validate SPL
spl3 validate ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-thinking/pocketflow-thinking.spl

# Step 4: Test SPL execution
spl3 run ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-thinking/pocketflow-thinking.spl \
  --adapter gemini_cli \
  --param question="Why is the speed of light constant in all reference frames?"

# Step 5: Compile to target runtime
spl3 splc compile ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-thinking/pocketflow-thinking.spl \
  --lang python/pocketflow \
  --out-dir ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-thinking/targets/

# Step 6: Test compiled implementation
python ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-thinking/targets/python_pocketflow/pocketflow-thinking_python_pocketflow.py \
  --question "Why is the speed of light constant in all reference frames?"
```

### Recipe 5: pocketflow-debate (Multi-Agent)

**Oracle**: `~/projects/digital-duck/PocketFlow/cookbook/pocketflow-debate/`

```bash
# Step 1: Extract specification
spl3 splc describe ~/projects/digital-duck/PocketFlow/cookbook/pocketflow-debate/ \
  --lang "Python — PocketFlow" --adapter gemini_cli \
  -o ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-debate/

# Step 2: Generate SPL
spl3 text2spl \
  --description ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-debate/flow-splc-python_pocketflow-spec.md \
  --mode workflow --adapter gemini_cli \
  -o ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-debate/pocketflow-debate.spl

# Step 3: Validate SPL
spl3 validate ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-debate/pocketflow-debate.spl

# Step 4: Test SPL execution
spl3 run ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-debate/pocketflow-debate.spl \
  --adapter gemini_cli \
  --param topic="AI will replace software engineers within 10 years"

# Step 5: Compile to target runtime
spl3 splc compile ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-debate/pocketflow-debate.spl \
  --lang python/pocketflow \
  --out-dir ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-debate/targets/

# Step 6: Test compiled implementation
python ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-debate/targets/python_pocketflow/pocketflow-debate_python_pocketflow.py \
  --topic "AI will replace software engineers within 10 years"
```

### Recipe 6: pocketflow-deep-research (Complex Research)

**Oracle**: `~/projects/digital-duck/PocketFlow/cookbook/pocketflow-deep-research/`

```bash
# Step 1: Extract specification
spl3 splc describe ~/projects/digital-duck/PocketFlow/cookbook/pocketflow-deep-research/ \
  --lang "Python — PocketFlow" --adapter gemini_cli \
  -o ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-deep-research/

# Step 2: Generate SPL
spl3 text2spl \
  --description ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-deep-research/flow-splc-python_pocketflow-spec.md \
  --mode workflow --adapter gemini_cli \
  -o ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-deep-research/pocketflow-deep-research.spl

# Step 3: Validate SPL
spl3 validate ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-deep-research/pocketflow-deep-research.spl

# Step 4: Test SPL execution
spl3 run ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-deep-research/pocketflow-deep-research.spl \
  --adapter gemini_cli \
  --param question="What are the latest developments in quantum computing?"

# Step 5: Compile to target runtime
spl3 splc compile ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-deep-research/pocketflow-deep-research.spl \
  --lang python/pocketflow \
  --out-dir ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-deep-research/targets/

# Step 6: Test compiled implementation
python ~/projects/digital-duck/SPL.py/cookbook-pocketflow-gemini/pocketflow-deep-research/targets/python_pocketflow/pocketflow-deep-research_python_pocketflow.py \
  --question "What are the latest developments in quantum computing?"
```

## Data Collection

### Metrics to Track

For each recipe, record:

```bash
# Create results tracking file
cat > recipe_results.md << 'EOF'
# Gemini CLI Adapter Results

## Recipe 1: pocketflow-agent
- [ ] splc describe: SUCCESS/FAILURE 
- [ ] text2spl: SUCCESS/FAILURE
- [ ] validate: SUCCESS/FAILURE  
- [ ] spl3 run: SUCCESS/FAILURE
- [ ] splc compile: SUCCESS/FAILURE
- [ ] python run: SUCCESS/FAILURE
- **Manual fixes**: [count]
- **Round-trip score**: [0.0-1.0]
- **Notes**: [observations]

## Recipe 2: pocketflow-rag
- [ ] splc describe: SUCCESS/FAILURE
- [ ] text2spl: SUCCESS/FAILURE
- [ ] validate: SUCCESS/FAILURE
- [ ] spl3 run: SUCCESS/FAILURE
- [ ] splc compile: SUCCESS/FAILURE
- [ ] python run: SUCCESS/FAILURE
- **Manual fixes**: [count]
- **Round-trip score**: [0.0-1.0] 
- **Notes**: [observations]

[... continue for all recipes ...]
