# Case 1 — gemma3 vs gemma4:12b on `symbolic_math.spl`

**Counter-point:** a bigger, newer model (`gemma4:12b`) is not automatically a
better fit for a workflow than a smaller, older one (`gemma3`). On this recipe,
`gemma3` won outright — it was faster, cheaper, *and* more reliable.

> One data point — not a benchmark. But it's a clean, reproducible illustration
> of why "use the biggest model available" is not a sound default for
> probabilistic steps inside a deterministic pipeline.

## The setup

`symbolic_math.spl` (recipe 67) asks an LLM to translate a natural-language math
question into a single terse line — `<expression>|<operation>` — which SymPy
then computes exactly. The prompt (`parse_math_problem`) is explicit:

> Reply with exactly one line in this format (no other text):
>   `<expression>|<operation>`

That contract — *terse, single-line, no reasoning preamble* — is the whole test.

## The three runs

### Run 1 — `gemma3`, compound prompt

```
spl3 run cookbook/67_symbolic_math/symbolic_math.spl \
    --adapter ollama --model gemma3 \
    --param problem="differentiate e**x and simplify it if necessary"
```

```
GENERATE segment 1 (parse_math_problem) -> 9 tokens, 1109ms
[INFO] Problem '@differentiate e**x and simplify it if necessary' is translated into SymPy:
 'exp(x)|diff, simplify'
...
Status:  complete
Output:  Okay, you asked us to find the derivative of the exponential function eˣ.
The symbolic engine tells us that the derivative of eˣ is simply eˣ itself! ...
LLM calls: 2  Latency: 3304ms
```

✅ **9 tokens, 1.1s** — terse, on-contract, and the workflow completes cleanly.

### Run 2 — `gemma4:12b`, same compound prompt

```
spl3 run cookbook/67_symbolic_math/symbolic_math.spl \
    --adapter ollama --model gemma4:12b \
    --param problem="differentiate e**x and simplify it if necessary"
```

```
GENERATE segment 1 (parse_math_problem) -> 1000 tokens, 43164ms
WARNING:spl.executor:GENERATE chain returned empty content for @parsed — variable unchanged
[INFO] Problem '@differentiate e**x and simplify it if necessary' is translated into SymPy:
 ''
...
Status:  complete
Output:  You were asking to find the derivative of the function $e^x$. The calculation
failed with a `SyntaxError`, meaning the system could not interpret the input as
a valid mathematical expression. ...
LLM calls: 2  Latency: 65602ms
```

❌ **1000 tokens (budget exhausted), 43s, empty `@parsed`.** The model burned its
entire generation budget and returned *nothing* the parser could use — the
`GENERATE chain returned empty content` warning fires, `@parsed` stays `''`,
SymPy never runs, and the final explanation is the model confabulating a
"SyntaxError" that never happened (the kernel never even got a chance to fail —
there was no expression to feed it).

### Run 3 — `gemma4:12b`, simpler prompt (no compound clause)

```
spl3 run cookbook/67_symbolic_math/symbolic_math.spl \
    --adapter ollama --model gemma4:12b \
    --param problem="differentiate e**x"
```

```
GENERATE segment 1 (parse_math_problem) -> 261 tokens, 10928ms
[INFO] Problem '@differentiate e**x' is translated into SymPy:
 'exp(x)|diff'
...
Status:  complete
Output:  You are looking for the rate of change (the derivative) of the
mathematical function $e^x$. The result of this calculation is exactly $e^x$. ...
LLM calls: 2  Latency: 28564ms
```

✅ Works — but even here it costs **261 tokens / 11s** vs. gemma3's 9 tokens for
an equivalent single-clause prompt.

## What the pattern shows

| Run | Model | Prompt | Tokens | Latency | `@parsed` |
|---|---|---|---|---|---|
| 1 | gemma3      | compound ("...and simplify it if necessary") | 9    | 1.1 s  | `exp(x)\|diff, simplify` ✅ |
| 2 | gemma4:12b  | compound (same)                               | 1000 | 43.2 s | `''` ❌ (budget exhausted, empty) |
| 3 | gemma4:12b  | simple ("differentiate e**x")                 | 261  | 10.9 s | `exp(x)\|diff` ✅ |

This is a **complexity cliff in instruction-following**, not a math-capability
gap — the LLM never does the math; SymPy does. The signature in run 2 (full
token budget consumed, zero usable output, `GENERATE chain returned empty
content`) is the classic shape of a model drifting into chain-of-thought /
reasoning preamble instead of obeying "reply with exactly one line, no other
text." `gemma3` honored that terse single-line contract immediately, on the
*harder* prompt; `gemma4:12b` only managed the contract once the prompt had no
compound clause left to reason about — and even then at ~29x the token cost of
gemma3's equivalent run.

In short: **bigger ≠ better-suited**. For a probabilistic step that's sandwiched
between two deterministic ones and bound by a strict output contract, the model
that follows the contract tersely and cheaply is the better fit — regardless of
which one scores higher on general benchmarks.

## The mitigation: shrink what any single LLM call has to absorb

`sympy_math_multi_step.spl` (in this same directory) is a structural answer to
exactly this failure mode: instead of asking one `GENERATE` to parse a compound
instruction ("differentiate ... and then simplify ...") into a correct
multi-operation line in one shot, it:

1. asks the LLM only to **decompose** the problem into an ordered list of
   *single*-operation steps (`<expression>|<operation>`, with `PREV` standing in
   for "the previous step's result"),
2. then runs each step through a reusable `solve_one_step` sub-`WORKFLOW`,
   `CALL`ed once per item — chaining the running expression deterministically
   (string substitution, never re-parsed by the LLM),
3. and only asks the LLM to **explain** the fully-computed, verified chain at
   the end.

Every individual LLM call stays as terse and single-clause as the prompts
gemma3 already handles cleanly in run 1 — the compound reasoning that tripped
up `gemma4:12b` never has to happen inside a single `GENERATE` at all.
