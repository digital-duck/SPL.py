# pocketflow-agent — SPL Port

ReAct-style agentic research loop ported from the
[PocketFlow](https://github.com/The-Pocket/PocketFlow) cookbook recipe `pocketflow-agent`.

## Pipeline used to generate this recipe

```
1. splc describe   ~/projects/wgong/PocketFlow/cookbook/pocketflow-agent/ \
                   --lang "Python — PocketFlow" --adapter claude_cli
                   → flow-splc-python_pocketflow-spec.md

2. text2spl        --description flow-splc-python_pocketflow-spec.md \
                   --mode workflow --adapter claude_cli \
                   -o pocketflow-agent.spl
                   → pocketflow-agent.spl  (Section 0 extracted automatically)

3. spl3 validate   pocketflow-agent.spl
                   → OK
```

Steps 1–3 were nearly fully automated. Only two minor manual fixes were needed:

| Fix | Root cause |
|-----|-----------|
| `INPUT: @max_iterations INTEGER := 8` — `:=` not accepted | `spl3` CLI was loading from SPL30 repo (stale editable install) instead of SPL.py — fixed by `pip install -e .` in SPL.py |
| EVALUATE branch: detect `"answer"` first, ELSE do search | LLM generated both `"search"` and `"answer"` branches explicitly — simplified to detect only the exit condition |

## How it works

```
START
  @context = "Initial question: " + @question
  @iteration = 0

  WHILE @iteration < @max_iterations:
    GENERATE DecideAction(@question, @context) → @decision

    EVALUATE @decision:
      WHEN contains('action: "answer"'):
        GENERATE AnswerQuestion(@question, @context) → @answer
        RETURN @answer  [status=complete]
      ELSE (search branch):
        GENERATE ExtractQuery(@decision) → @query
        GENERATE SearchWeb(@query) → @search_results
        @context += search_results
        @iteration += 1

  # fallback if max_iterations reached
  GENERATE AnswerQuestion(@question, @context) → @answer
  RETURN @answer  [status=max_iterations]

EXCEPTION BudgetExceeded:
  RETURN best answer so far  [status=budget_limit]
```

## Run

### Ollama

```bash
spl3 run ./cookbook-pocketflow/pocketflow-agent/pocketflow-agent.spl \
  --adapter ollama \
  --param max_iterations=3 \
  --tools cookbook-pocketflow/pocketflow-agent/tools.py \
  --param question="Who won the Nobel Prize in Physics 2024?"

```

```output
<pre>Status:  complete
Output:  I&apos;m sorry but I can&apos;t answer this year&apos;s question as it&apos;s not yet known. However, I can provide some general information about the Nobel Prize in Physics.

The Nobel Prize in Physics is one of the most prestigious awards in the field of physics, established by Alfred Nobel in 1901. It is awarded annually to recognize outstanding contributions in the field of physics.

The winners of the Nobel Prize in Physics are selected by a committee of experts in the field, and the announcement is typically made on October 8th of each year. The prize is awarded to individuals or organizations who have made significant discoveries or advancements in the field of physics.

In recent years, some notable winners of the Nobel Prize in Physics include:

* 2022: Alain Aspect, John F. Clauser, and Anton Zeilinger for their experiments with entangled photons
* 2021: Syukuro Manabe, Klaus Hasselmann, and Giorgio Parisi for their contributions to our understanding of complex systems
* 2020: Roger Penrose, Reinhard Genzel, and Andrea
LLM calls: 2  Latency: 8139ms
Log:     /home/gong2/.spl/logs/pocketflow_agent-ollama-20260426-224538.md
```

**Note:**

The gemma3 failure is expected — small local models often can't reconcile search snippets with their (incorrect) priors.    
  Claude will use the real search results and give the correct answer (John Hopfield + Geoffrey Hinton).


### Claude_cli


```bash
spl3 run ./cookbook-pocketflow/pocketflow-agent/pocketflow-agent.spl \
  --adapter claude_cli \
  --param max_iterations=3 \
  --tools cookbook-pocketflow/pocketflow-agent/tools.py \
  --param question="Who won the Nobel Prize in Physics 2024?"


```

```output
INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook-pocketflow/pocketflow-agent/pocketflow-agent.spl
Registry: ['react_research']
Loaded 62 tool(s) from cookbook-pocketflow/pocketflow-agent/tools.py
Running workflow: react_research(['max_iterations', 'question'])
INFO:spl.executor:GENERATE segment 1 (DecideAction) -> 261 tokens, 9270ms
INFO:spl.executor:GENERATE chain done -> @decision (1047 chars total)
INFO:spl.executor:GENERATE segment 1 (AnswerQuestion) -> 295 tokens, 9802ms
INFO:spl.executor:GENERATE chain done -> @answer (1182 chars total)
INFO:spl.executor:RETURN: 1182 chars | status=complete, iterations=0

Status:  complete
Output:  The **2024 Nobel Prize in Physics** was awarded to:

- **John J. Hopfield** (Princeton University, USA)
- **Geoffrey E. Hinton** (University of Toronto, Canada)

**For:** *foundational discoveries and inventions that enable machine learning with artificial neural networks*

### Key Contributions

**John Hopfield** invented the **Hopfield network** (1982) — an associative memory network that can store and reconstruct patterns, inspired by how physicists model spin systems in materials.

**Geoffrey Hinton** developed the **Boltzmann machine** (with David Rumelhart and Ronald Williams), a generative model that learned to find hidden structure in data. He also co-developed **backpropagation**, the algorithm that made training deep neural networks practical.

### Significance

The Royal Swedish Academy of Sciences recognized that their work from the 1980s laid the groundwork for the modern deep learning revolution — the foundation behind today's AI systems including image recognition, language models, and much more.

Notably, Hinton had left Google in 2023 to speak freely about AI risks, and his Nobel win drew significant attention given his public stance on AI safety.
LLM calls: 2  Latency: 19075ms
Log:     /home/gong2/.spl/logs/pocketflow_agent-claude_cli-20260426-224418.md

```



## Tools

`web_search` is implemented in `tools.py` using DuckDuckGo (`ddgs` package) and registered
via `@spl_tool`.  The SPL workflow calls it directly:

```spl
CALL web_search(@decision) INTO @search_results;
```

The tool auto-extracts the `search_query:` field from the YAML decision block, so `@decision`
can be passed directly without a separate `ExtractQuery` step.

## Files

| File | Description |
|------|-------------|
| `pocketflow-agent.spl` | SPL 3.0 workflow script |
| `flow-splc-python_pocketflow-spec.md` | Spec generated by `splc describe` (oracle) |

## Oracle (original PocketFlow recipe)

`~/projects/wgong/PocketFlow/cookbook/pocketflow-agent/`


# SPLc compile

```bash
cd ~/projects/digital-duck/SPL.py
spl3 splc compile ./cookbook-pocketflow/pocketflow-agent/pocketflow-agent.spl \
  --lang python/pocketflow \
  --overwrite \
  --model claude-sonnet-4-6

# Force LLM compilation even when a deterministic transpiler is available
  --llm

```


## test

```bash
pip install pocketflow click

python ./cookbook-pocketflow/pocketflow-agent/targets/python_pocketflow/pocketflow-agent_python_pocketflow.py \
  --question "who won 2024 Nobel Prize in Physics"
```


```output
Deciding next action ...
Searching the web ...
Deciding next action ...
Searching the web ...
Deciding next action ...
Searching the web ...
Deciding next action ...
Generating final answer ...

Status:     max_iterations
Iterations: 3

I must correct you - since my knowledge cutoff is December 2023, I do not have information on the 2024 Nobel Prize in Physics.

However, I can provide some context and insights based on previous years' winners and notable research in physics.

The Nobel Prize in Physics is awarded annually by the Royal Swedish Academy of Sciences to recognize outstanding contributions in the field of physics. The prize has been awarded since 1901, with the first winner being Wilhelm Conrad Röntgen for his discovery of X-rays.

In recent years, the Nobel Prize in Physics has been awarded to notable physicists such as:

* 2022: Alain Aspect, John F. Clauser, and Anton Zeilinger for their experiments with entangled particles
* 2021: Syukuno Sasaki and Klaus Hasselmann, along with Giorgio Parisi, for their work on quantum field theory and condensed matter physics
* 2018: Arthur Ashkin, Gérard Mourou, and Donna Strickland for their contributions to the development of laser technology

The Nobel Prize in Physics has also been awarded to several notable researchers who have made significant contributions to our understanding of the universe. Some examples include:

* Stephen Hawking, who was awarded the prize in 1974 for his work on black holes
* Richard Feynman, who was awarded the prize in 1965 for his work on quantum electrodynamics
* Marie Curie, who was awarded the prize in 1903 and 1911 for her groundbreaking research on radioactivity

While I do not have information on the 2024 Nobel Prize in Physics, I encourage you to check the official Nobel Prize website or reputable news sources for updates on this year's winners.


```


```bash
(base) gong2@gong2:~/projects/digital-duck/SPL.py$ python ./cookbook-pocketflow/pocketflow-agent/targets/python_pocketflow/pocketflow-agent_python_pocketflow.py   --question "who won 2020 Nobel Prize in Physics"
```

Deciding next action ...
Searching the web ...
Deciding next action ...
Searching the web ...
Deciding next action ...
Searching the web ...
Deciding next action ...
Generating final answer ...

Status:     max_iterations
Iterations: 3

The 2020 Nobel Prize in Physics was awarded to Roger Penrose, Reinhard Genzel, and Andrea Ghez for their groundbreaking contributions to our understanding of black holes.

Roger Penrose, a British mathematician and physicist, was recognized for his work on the theoretical foundations of black hole physics. Specifically, his 1964 paper "The Large Scale Structure of Space-Time" proposed that singularities, such as those found at the centers of black holes, are mathematically impossible (Penrose, 1964). This idea challenged the traditional view of spacetime and had significant implications for our understanding of gravity and the behavior of matter in extreme environments.

Reinhard Genzel and Andrea Ghez were awarded the prize for their pioneering work on the observational evidence for black holes at the centers of galaxies. Through their observations with the Keck Observatory in Hawaii, they detected a supermassive black hole at the center of the galaxy Messier 87 (M87), which is located approximately 55 million light-years away from Earth (Genzel et al., 2018). This discovery provided strong evidence for the existence of these objects and shed new light on their role in the evolution of galaxies.

The 2020 Nobel Prize in Physics was awarded in recognition of the significant contributions made by Penrose, Genzel, and Ghez to our understanding of black hole physics. Their work has had far-reaching implications for fields such as astrophysics, cosmology, and theoretical physics (Nobel Foundation, 2020).

References:

Genzel, R., et al. (2018). First M87 Event Horizon Telescope Results: IV. The Shadow of the Supermassive Black Hole. The Astrophysical Journal Letters, 875(1), L1-L9.

Penrose, R. (1964). The Large Scale Structure of Space-Time. Reviews of Modern Physics, 36(3), 421-437.

Nobel Foundation. (2020). Nobel Prize in Physics 2020. Retrieved from <https://www.nobelprize.org/prizes/physics/2020/

This comprehensive answer provides a thorough overview of the research and contributions that led to the awarding of the 2020 Nobel Prize in Physics. It highlights the key findings and work of Roger Penrose, Reinhard Genzel, and Andrea Ghez, and references relevant sources from the scientific community.
