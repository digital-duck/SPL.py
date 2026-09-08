# Recipe-77 Momagrid experiment run 20260620-205109

DB source: `exp-momagrid-20260620-205109`
Momagrid Hub: http://192.168.0.170:9000/
Workers: 3


## gemma3 (ollama) — backend=sympy — solver=true — run 1

_Tier: T0 | Problem ID: `p001` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma3 \
   --param problem="differentiate x**4 - 2*x**2 + 1" \
   --param hostname="mac-wens-Mac-mini.local" \
   --param backend=sympy \
   --param enable_solver=true
```

```output

## gemma3 (ollama) — backend=sympy — solver=true — run 1

_Tier: T0 | Problem ID: `p011` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma3 \
   --param problem="simplify the rational expression (x**2 - 1) / (x - 1)" \
   --param hostname="mac-wens-Mac-mini.local" \
   --param backend=sympy \
   --param enable_solver=true
```

```output

## gemma3 (ollama) — backend=sympy — solver=true — run 1

_Tier: T1 | Problem ID: `p002` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma3 \
   --param problem="expand (x+1)**2, then factor the expanded form" \
   --param hostname="mac-wens-Mac-mini.local" \
   --param backend=sympy \
   --param enable_solver=true
```

```output
INFO:spl.registry:Registry: loaded 2 workflow(s) from cookbook/77_neurosymbolic/symbolic_math.spl
INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/77_neurosymbolic/sympolic_tools.spl
Registry: ['neurosymbolic_solver', 'solve_chain_step']
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
IPython kernel: enabled (name=python3, scope=session, timeout=60.0s)
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
Running workflow: neurosymbolic_solver(['problem', 'hostname', 'backend', 'enable_solver', 'model'])
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sympy solver=true
[INFO] [arm=solver] Problem 'expand (x+1)**2, then factor the expanded form' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 31ef887b-a73c-4609-87c9-91c601c74d50 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/31ef887b-a73c-4609-87c9-91c601c74d50 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/31ef887b-a73c-4609-87c9-91c601c74d50 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/31ef887b-a73c-4609-87c9-91c601c74d50 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 31ef887b-a73c-4609-87c9-91c601c74d50 completed by agent papa-game in 1643ms (16 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 16 tokens, 4045ms
INFO:spl.executor:GENERATE chain done -> @steps_text (30 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


(x + 1)**2|expand
PREV|factor


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 50 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 139ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] expand((x + 1)**2) = x**2 + 2*x + 1
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 46 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] factor(x**2 + 2*x + 1) = (x + 1)**2
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 4f4ae0fc-5baa-4263-95d2-d48ab0a98474 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/4f4ae0fc-5baa-4263-95d2-d48ab0a98474 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/4f4ae0fc-5baa-4263-95d2-d48ab0a98474 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/4f4ae0fc-5baa-4263-95d2-d48ab0a98474 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/4f4ae0fc-5baa-4263-95d2-d48ab0a98474 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 4f4ae0fc-5baa-4263-95d2-d48ab0a98474 completed by agent papa-game in 3026ms (125 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 125 tokens, 6030ms
INFO:spl.executor:GENERATE chain done -> @result (438 chars total)
INFO:spl.executor:RETURN: 438 chars | status=complete, arm=solver, backend=sympy, steps=2

Status:  complete
Output:  Okay, let’s break down this math problem! We need to take a simple expression – (x + 1)**2 – and fully simplify it by expanding and then factoring it out. First, we expand that expression: (x + 1)**2 results in x**2 + 2*x + 1. Next, we factor the expanded form, which gives us (x + 1)**2. This is because it’s a perfect square trinomial – essentially, it factors back into two identical terms.  So, the final answer is simply (x + 1)**2 .
LLM calls: 2  Latency: 10217ms
Workers: papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-205109.md
```


## gemma3 (ollama) — backend=sympy — solver=true — run 1

_Tier: T1 | Problem ID: `p003` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma3 \
   --param problem="differentiate 3*x**3-x, then factor if needed, finally solve for x" \
   --param hostname="mac-wens-Mac-mini.local" \
   --param backend=sympy \
   --param enable_solver=true
```

```output
INFO:spl.registry:Registry: loaded 2 workflow(s) from cookbook/77_neurosymbolic/symbolic_math.spl
INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/77_neurosymbolic/sympolic_tools.spl
Registry: ['neurosymbolic_solver', 'solve_chain_step']
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
IPython kernel: enabled (name=python3, scope=session, timeout=60.0s)
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
Running workflow: neurosymbolic_solver(['problem', 'hostname', 'backend', 'enable_solver', 'model'])
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sympy solver=true
[INFO] [arm=solver] Problem 'simplify the rational expression (x**2 - 1) / (x - 1)' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 168aa1de-583b-4a8c-b7fa-f8e8ddb0ff5e submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/168aa1de-583b-4a8c-b7fa-f8e8ddb0ff5e "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/168aa1de-583b-4a8c-b7fa-f8e8ddb0ff5e "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/168aa1de-583b-4a8c-b7fa-f8e8ddb0ff5e "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/168aa1de-583b-4a8c-b7fa-f8e8ddb0ff5e "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/168aa1de-583b-4a8c-b7fa-f8e8ddb0ff5e "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 168aa1de-583b-4a8c-b7fa-f8e8ddb0ff5e completed by agent mac-wens-Mac-mini.local in 5800ms (23 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 23 tokens, 8066ms
INFO:spl.executor:GENERATE chain done -> @steps_text (44 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


(x**2 - 1) / (x - 1)|simplify
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 44 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 169ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] simplify((x**2 - 1) / (x - 1)) = x + 1
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 29 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] simplify(x + 1) = x + 1
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task a9197658-b7d4-4eab-9ddc-932d5f1608db submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a9197658-b7d4-4eab-9ddc-932d5f1608db "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a9197658-b7d4-4eab-9ddc-932d5f1608db "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a9197658-b7d4-4eab-9ddc-932d5f1608db "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task a9197658-b7d4-4eab-9ddc-932d5f1608db completed by agent papa-game in 2678ms (119 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 119 tokens, 4026ms
INFO:spl.executor:GENERATE chain done -> @result (376 chars total)
INFO:spl.executor:RETURN: 376 chars | status=complete, arm=solver, backend=sympy, steps=2

Status:  complete
Output:  Okay, let’s simplify the rational expression (x² - 1) / (x - 1). First, we recognize that x² - 1 is a difference of squares and can be factored into (x - 1)(x + 1).  Therefore, the expression becomes (x - 1)(x + 1) / (x - 1). Next, we can cancel out one of the (x - 1) terms from the numerator and denominator, resulting in x + 1. Finally, this simplified expression is x + 1.
LLM calls: 2  Latency: 12265ms
Workers: mac-wens-Mac-mini.local, papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-205109.md
```


## gemma3 (ollama) — backend=sympy — solver=true — run 1

_Tier: T1 | Problem ID: `p004` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma3 \
   --param problem="expand (x-2)**3, then differentiate the result, then simplify it, then factor that, then solve for x = 0" \
   --param hostname="mac-wens-Mac-mini.local" \
   --param backend=sympy \
   --param enable_solver=true
```

```output
INFO:spl.registry:Registry: loaded 2 workflow(s) from cookbook/77_neurosymbolic/symbolic_math.spl
INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/77_neurosymbolic/sympolic_tools.spl
Registry: ['neurosymbolic_solver', 'solve_chain_step']
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
IPython kernel: enabled (name=python3, scope=session, timeout=60.0s)
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
Running workflow: neurosymbolic_solver(['problem', 'hostname', 'backend', 'enable_solver', 'model'])
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sympy solver=true
[INFO] [arm=solver] Problem 'differentiate 3*x**3-x, then factor if needed, finally solve for x' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task ce2d3c5e-3c1c-4606-b59d-c1b436a73f8b submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ce2d3c5e-3c1c-4606-b59d-c1b436a73f8b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ce2d3c5e-3c1c-4606-b59d-c1b436a73f8b "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task ce2d3c5e-3c1c-4606-b59d-c1b436a73f8b completed by agent mac-wens-Mac-mini.local in 993ms (20 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 20 tokens, 2027ms
INFO:spl.executor:GENERATE chain done -> @steps_text (38 chars total)
[INFO] [arm=solver] decomposed into 3 step(s):


3*x**3 - x|diff
PREV|factor
PREV|solve


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 40 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 112ms (0 LLM calls)
[INFO] [arm=solver][step 1/3] d/dx(3*x**3 - x) = 9*x**2 - 1
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 60 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 2/3] factor(9*x**2 - 1) = (3*x - 1)*(3*x + 1)
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 61 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 3/3] solve((3*x - 1)*(3*x + 1) = 0) -> x = [-1/3, 1/3]
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 12c67bdf-5f37-4a4a-88c9-1e6555fe6323 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/12c67bdf-5f37-4a4a-88c9-1e6555fe6323 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/12c67bdf-5f37-4a4a-88c9-1e6555fe6323 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/12c67bdf-5f37-4a4a-88c9-1e6555fe6323 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/12c67bdf-5f37-4a4a-88c9-1e6555fe6323 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 12c67bdf-5f37-4a4a-88c9-1e6555fe6323 completed by agent mac-wens-Mac-mini.local in 4071ms (120 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 120 tokens, 6035ms
INFO:spl.executor:GENERATE chain done -> @result (441 chars total)
INFO:spl.executor:RETURN: 441 chars | status=complete, arm=solver, backend=sympy, steps=3

Status:  complete
Output:  Okay, let’s break down this problem! We were asked to find the derivative of the expression 3*x**3 - x, and then solve for the values of *x* that make the resulting equation equal to zero after factoring. First, we differentiated the original expression obtaining 9*x**2 - 1. Next, we factored this quadratic expression into (3*x - 1)*(3*x + 1). Finally, setting this factored form equal to zero gives us two solutions: x = -1/3 and x = 1/3.
LLM calls: 2  Latency: 8178ms
Workers: mac-wens-Mac-mini.local
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-205120.md
```


## gemma3 (ollama) — backend=sympy — solver=true — run 1

_Tier: T1 | Problem ID: `p012` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma3 \
   --param problem="find the partial fraction decomposition of 1 / (x**2 - 1)" \
   --param hostname="mac-wens-Mac-mini.local" \
   --param backend=sympy \
   --param enable_solver=true
```

```output
INFO:spl.registry:Registry: loaded 2 workflow(s) from cookbook/77_neurosymbolic/symbolic_math.spl
INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/77_neurosymbolic/sympolic_tools.spl
Registry: ['neurosymbolic_solver', 'solve_chain_step']
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
IPython kernel: enabled (name=python3, scope=session, timeout=60.0s)
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
Running workflow: neurosymbolic_solver(['problem', 'hostname', 'backend', 'enable_solver', 'model'])
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sympy solver=true
[INFO] [arm=solver] Problem 'expand (x-2)**3, then differentiate the result, then simplify it, then factor that, then solve for x = 0' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 911e82d1-cb3c-4f6b-b05c-80ca17e61036 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/911e82d1-cb3c-4f6b-b05c-80ca17e61036 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/911e82d1-cb3c-4f6b-b05c-80ca17e61036 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/911e82d1-cb3c-4f6b-b05c-80ca17e61036 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 911e82d1-cb3c-4f6b-b05c-80ca17e61036 completed by agent papa-game in 2070ms (31 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 31 tokens, 4035ms
INFO:spl.executor:GENERATE chain done -> @steps_text (65 chars total)
[INFO] [arm=solver] decomposed into 5 step(s):


(x - 2)**3|expand
PREV|diff
PREV|simplify
PREV|factor
PREV|solve


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 70 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 145ms (0 LLM calls)
[INFO] [arm=solver][step 1/5] expand((x - 2)**3) = x**3 - 6*x**2 + 12*x - 8
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 70 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 3ms (0 LLM calls)
[INFO] [arm=solver][step 2/5] d/dx(x**3 - 6*x**2 + 12*x - 8) = 3*x**2 - 12*x + 12
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 68 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 31ms (0 LLM calls)
[INFO] [arm=solver][step 3/5] simplify(3*x**2 - 12*x + 12) = 3*x**2 - 12*x + 12
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 54 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 4/5] factor(3*x**2 - 12*x + 12) = 3*(x - 2)**2
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 38 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 2ms (0 LLM calls)
[INFO] [arm=solver][step 5/5] solve(3*(x - 2)**2 = 0) -> x = [2]
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 4184262b-3630-4fe9-8de1-7d05b676ffb8 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/4184262b-3630-4fe9-8de1-7d05b676ffb8 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/4184262b-3630-4fe9-8de1-7d05b676ffb8 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/4184262b-3630-4fe9-8de1-7d05b676ffb8 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/4184262b-3630-4fe9-8de1-7d05b676ffb8 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 4184262b-3630-4fe9-8de1-7d05b676ffb8 completed by agent papa-game in 3767ms (156 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 156 tokens, 6036ms
INFO:spl.executor:GENERATE chain done -> @result (463 chars total)
INFO:spl.executor:RETURN: 463 chars | status=complete, arm=solver, backend=sympy, steps=5

Status:  complete
Output:  Okay, let's break down this problem! We’re essentially trying to find the value of ‘x’ that makes the expression `3*(x - 2)**2` equal to zero. First, we expanded it to `x**3 - 6*x**2 + 12*x - 8`. Then, we took the derivative of this polynomial which yielded `3*x**2 - 12*x + 12`. Simplifying this gave us `3*x**2 - 12*x + 12` and factoring it produced `3*(x - 2)**2`. Finally, setting this equal to zero and solving for ‘x’ resulted in the single solution: x = 2.
LLM calls: 2  Latency: 10256ms
Workers: papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-205122.md
```


## gemma3 (ollama) — backend=sympy — solver=true — run 1

_Tier: T2 | Problem ID: `p005` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma3 \
   --param problem="differentiate exp(x) and simplify it if necessary" \
   --param hostname="mac-wens-Mac-mini.local" \
   --param backend=sympy \
   --param enable_solver=true
```

```output
INFO:spl.registry:Registry: loaded 2 workflow(s) from cookbook/77_neurosymbolic/symbolic_math.spl
INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/77_neurosymbolic/sympolic_tools.spl
Registry: ['neurosymbolic_solver', 'solve_chain_step']
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
IPython kernel: enabled (name=python3, scope=session, timeout=60.0s)
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
Running workflow: neurosymbolic_solver(['problem', 'hostname', 'backend', 'enable_solver', 'model'])
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sympy solver=true
[INFO] [arm=solver] Problem 'find the partial fraction decomposition of 1 / (x**2 - 1)' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task a9304037-03f5-484e-9653-1669cc31cd76 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a9304037-03f5-484e-9653-1669cc31cd76 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a9304037-03f5-484e-9653-1669cc31cd76 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task a9304037-03f5-484e-9653-1669cc31cd76 completed by agent mac-wens-Mac-mini.local in 913ms (17 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 17 tokens, 2029ms
INFO:spl.executor:GENERATE chain done -> @steps_text (30 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


1/(x**2 - 1)|apart
PREV|apart


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 83 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 140ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] apart(1/(x**2 - 1)) = -1/(2*(x + 1)) + 1/(2*(x - 1))
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 101 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 2ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] apart(-1/(2*(x + 1)) + 1/(2*(x - 1))) = -1/(2*(x + 1)) + 1/(2*(x - 1))
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 2bd1f104-3e94-4700-9d78-9af5808168cf submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2bd1f104-3e94-4700-9d78-9af5808168cf "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2bd1f104-3e94-4700-9d78-9af5808168cf "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2bd1f104-3e94-4700-9d78-9af5808168cf "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2bd1f104-3e94-4700-9d78-9af5808168cf "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 2bd1f104-3e94-4700-9d78-9af5808168cf completed by agent mac-wens-Mac-mini.local in 5735ms (181 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 181 tokens, 6037ms
INFO:spl.executor:GENERATE chain done -> @result (526 chars total)
INFO:spl.executor:RETURN: 526 chars | status=complete, arm=solver, backend=sympy, steps=2

Status:  complete
Output:  Okay, let's break down how to find the partial fraction decomposition of 1 / (x² - 1). We want to express this complex fraction as a sum of simpler fractions. First, the symbolic engine recognized that we could factor the denominator:  `apart(1/(x**2 - 1)) = -1/(2*(x + 1)) + 1/(2*(x - 1))` . Then, it simply verified that the expression remains unchanged with `apart(-1/(2*(x + 1)) + 1/(2*(x - 1))) = -1/(2*(x + 1)) + 1/(2*(x - 1))`.  Therefore, the partial fraction decomposition is:  -1 / (2 * (x + 1)) + 1 / (2 * (x - 1)).
LLM calls: 2  Latency: 8210ms
Workers: mac-wens-Mac-mini.local
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-205129.md
```


## gemma3 (ollama) — backend=sympy — solver=true — run 1

_Tier: T2 | Problem ID: `p006` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma3 \
   --param problem="find the limit of sin(x) divided by x as x approaches 0" \
   --param hostname="mac-wens-Mac-mini.local" \
   --param backend=sympy \
   --param enable_solver=true
```

```output
INFO:spl.registry:Registry: loaded 2 workflow(s) from cookbook/77_neurosymbolic/symbolic_math.spl
INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/77_neurosymbolic/sympolic_tools.spl
Registry: ['neurosymbolic_solver', 'solve_chain_step']
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
IPython kernel: enabled (name=python3, scope=session, timeout=60.0s)
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
Running workflow: neurosymbolic_solver(['problem', 'hostname', 'backend', 'enable_solver', 'model'])
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sympy solver=true
[INFO] [arm=solver] Problem 'differentiate exp(x) and simplify it if necessary' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 96a0d89b-27eb-4ff0-926b-e34ec3c454a6 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/96a0d89b-27eb-4ff0-926b-e34ec3c454a6 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/96a0d89b-27eb-4ff0-926b-e34ec3c454a6 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/96a0d89b-27eb-4ff0-926b-e34ec3c454a6 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 96a0d89b-27eb-4ff0-926b-e34ec3c454a6 completed by agent papa-game in 1375ms (12 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 12 tokens, 4028ms
INFO:spl.executor:GENERATE chain done -> @steps_text (26 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


exp(x)|diff
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 28 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 112ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] d/dx(exp(x)) = exp(x)
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 32 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 44ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] simplify(exp(x)) = exp(x)
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task cc6fa63d-35f4-4617-b44e-00e44cc50051 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/cc6fa63d-35f4-4617-b44e-00e44cc50051 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/cc6fa63d-35f4-4617-b44e-00e44cc50051 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/cc6fa63d-35f4-4617-b44e-00e44cc50051 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/cc6fa63d-35f4-4617-b44e-00e44cc50051 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task cc6fa63d-35f4-4617-b44e-00e44cc50051 completed by agent papa-game in 2702ms (104 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 104 tokens, 6037ms
INFO:spl.executor:GENERATE chain done -> @result (422 chars total)
INFO:spl.executor:RETURN: 422 chars | status=complete, arm=solver, backend=sympy, steps=2

Status:  complete
Output:  Okay, let's break down this problem! We’re essentially asking to find the derivative of the exponential function `exp(x)` and then simplify it. First, we take the derivative of `exp(x)`, which results in `exp(x)`.  Next, we simply leave the result as is, because the derivative of an exponential function remains itself. Therefore, the simplified form of the derivative is still `exp(x)`. So, the final answer is `exp(x)`.
LLM calls: 2  Latency: 10221ms
Workers: papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-205133.md
```


## gemma3 (ollama) — backend=sympy — solver=true — run 1

_Tier: T2 | Problem ID: `p013` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma3 \
   --param problem="expand sin(x) as a Taylor series around x = 0, keeping terms up to degree 5" \
   --param hostname="mac-wens-Mac-mini.local" \
   --param backend=sympy \
   --param enable_solver=true
```

```output
INFO:spl.registry:Registry: loaded 2 workflow(s) from cookbook/77_neurosymbolic/symbolic_math.spl
INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/77_neurosymbolic/sympolic_tools.spl
Registry: ['neurosymbolic_solver', 'solve_chain_step']
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
IPython kernel: enabled (name=python3, scope=session, timeout=60.0s)
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
Running workflow: neurosymbolic_solver(['problem', 'hostname', 'backend', 'enable_solver', 'model'])
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sympy solver=true
[INFO] [arm=solver] Problem 'find the limit of sin(x) divided by x as x approaches 0' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 76cf1203-95a9-44dc-8bd2-6338bf4996f3 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/76cf1203-95a9-44dc-8bd2-6338bf4996f3 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/76cf1203-95a9-44dc-8bd2-6338bf4996f3 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/76cf1203-95a9-44dc-8bd2-6338bf4996f3 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 76cf1203-95a9-44dc-8bd2-6338bf4996f3 completed by agent mac-wens-Mac-mini.local in 948ms (19 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 19 tokens, 4045ms
INFO:spl.executor:GENERATE chain done -> @steps_text (34 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


sin(x)/x|limit(x,0)
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 27 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 126ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] limit(sin(x)/x, x->0) = 1
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 17 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] simplify(1) = 1
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task e2f0755c-3983-4d2c-8a26-b427438ec75a submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/e2f0755c-3983-4d2c-8a26-b427438ec75a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/e2f0755c-3983-4d2c-8a26-b427438ec75a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/e2f0755c-3983-4d2c-8a26-b427438ec75a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/e2f0755c-3983-4d2c-8a26-b427438ec75a "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task e2f0755c-3983-4d2c-8a26-b427438ec75a completed by agent mac-wens-Mac-mini.local in 3538ms (105 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 105 tokens, 6028ms
INFO:spl.executor:GENERATE chain done -> @result (425 chars total)
INFO:spl.executor:RETURN: 425 chars | status=complete, arm=solver, backend=sympy, steps=2

Status:  complete
Output:  Okay, let’s tackle this problem: we want to find what value sin(x) approaches as x gets incredibly close to zero. The symbolic engine first identified the limit of sin(x)/x as x approaching 0 as being equal to 1.  It then simplified that result, confirming it remains 1. This process essentially tells us that as x shrinks towards zero, the ratio of sine(x) to x gets closer and closer to 1. Therefore, the final answer is 1.
LLM calls: 2  Latency: 10202ms
Workers: mac-wens-Mac-mini.local
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-205137.md
```


## gemma3 (ollama) — backend=sympy — solver=true — run 1

_Tier: T2 | Problem ID: `p014` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma3 \
   --param problem="simplify sin(x)**2 + cos(x)**2 using trigonometric identities" \
   --param hostname="mac-wens-Mac-mini.local" \
   --param backend=sympy \
   --param enable_solver=true
```

```output
INFO:spl.registry:Registry: loaded 2 workflow(s) from cookbook/77_neurosymbolic/symbolic_math.spl
INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/77_neurosymbolic/sympolic_tools.spl
Registry: ['neurosymbolic_solver', 'solve_chain_step']
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
IPython kernel: enabled (name=python3, scope=session, timeout=60.0s)
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
Running workflow: neurosymbolic_solver(['problem', 'hostname', 'backend', 'enable_solver', 'model'])
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sympy solver=true
[INFO] [arm=solver] Problem 'differentiate x**4 - 2*x**2 + 1' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 059e62b6-f4d7-4acf-bd71-19c6ef00fd47 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/059e62b6-f4d7-4acf-bd71-19c6ef00fd47 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/059e62b6-f4d7-4acf-bd71-19c6ef00fd47 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/059e62b6-f4d7-4acf-bd71-19c6ef00fd47 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/059e62b6-f4d7-4acf-bd71-19c6ef00fd47 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/059e62b6-f4d7-4acf-bd71-19c6ef00fd47 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/059e62b6-f4d7-4acf-bd71-19c6ef00fd47 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/059e62b6-f4d7-4acf-bd71-19c6ef00fd47 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/059e62b6-f4d7-4acf-bd71-19c6ef00fd47 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/059e62b6-f4d7-4acf-bd71-19c6ef00fd47 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/059e62b6-f4d7-4acf-bd71-19c6ef00fd47 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/059e62b6-f4d7-4acf-bd71-19c6ef00fd47 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/059e62b6-f4d7-4acf-bd71-19c6ef00fd47 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/059e62b6-f4d7-4acf-bd71-19c6ef00fd47 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/059e62b6-f4d7-4acf-bd71-19c6ef00fd47 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/059e62b6-f4d7-4acf-bd71-19c6ef00fd47 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/059e62b6-f4d7-4acf-bd71-19c6ef00fd47 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/059e62b6-f4d7-4acf-bd71-19c6ef00fd47 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/059e62b6-f4d7-4acf-bd71-19c6ef00fd47 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/059e62b6-f4d7-4acf-bd71-19c6ef00fd47 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/059e62b6-f4d7-4acf-bd71-19c6ef00fd47 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/059e62b6-f4d7-4acf-bd71-19c6ef00fd47 "HTTP/1.1 200 OK"

Aborted!
```


## gemma3 (ollama) — backend=sage — solver=true — run 1

_Tier: T3 | Problem ID: `p007` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma3 \
   --param problem="integrate the square root of (4 minus x squared)" \
   --param hostname="mac-wens-Mac-mini.local" \
   --param backend=sage \
   --param enable_solver=true
```

```output
INFO:spl.registry:Registry: loaded 2 workflow(s) from cookbook/77_neurosymbolic/symbolic_math.spl
INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/77_neurosymbolic/sympolic_tools.spl
Registry: ['neurosymbolic_solver', 'solve_chain_step']
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
IPython kernel: enabled (name=python3, scope=session, timeout=60.0s)
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
Running workflow: neurosymbolic_solver(['problem', 'hostname', 'backend', 'enable_solver', 'model'])
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sympy solver=true
[INFO] [arm=solver] Problem 'simplify sin(x)**2 + cos(x)**2 using trigonometric identities' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 741c38f4-f659-499f-a8ca-721ea087cd39 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/741c38f4-f659-499f-a8ca-721ea087cd39 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/741c38f4-f659-499f-a8ca-721ea087cd39 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 741c38f4-f659-499f-a8ca-721ea087cd39 completed by agent papa-game in 1028ms (18 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 18 tokens, 2028ms
INFO:spl.executor:GENERATE chain done -> @steps_text (36 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


sin(x)**2 + cos(x)**2|simplify
PREV


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 37 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 184ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] simplify(sin(x)**2 + cos(x)**2) = 1
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 18 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] 1 (pass-through)

Aborted!
```


## gemma3 (ollama) — backend=sage — solver=true — run 1

_Tier: T3 | Problem ID: `p008` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma3 \
   --param problem="find the integral of sin(x) times cos(x), then simplify the result" \
   --param hostname="mac-wens-Mac-mini.local" \
   --param backend=sage \
   --param enable_solver=true
```

```output
INFO:spl.registry:Registry: loaded 2 workflow(s) from cookbook/77_neurosymbolic/symbolic_math.spl
INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/77_neurosymbolic/sympolic_tools.spl
Registry: ['neurosymbolic_solver', 'solve_chain_step']
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
IPython kernel: enabled (name=python3, scope=session, timeout=60.0s)
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
Running workflow: neurosymbolic_solver(['problem', 'hostname', 'backend', 'enable_solver', 'model'])
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sympy solver=true
[INFO] [arm=solver] Problem 'expand sin(x) as a Taylor series around x = 0, keeping terms up to degree 5' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task c54767b6-45db-4414-bb95-72619151a004 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/c54767b6-45db-4414-bb95-72619151a004 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/c54767b6-45db-4414-bb95-72619151a004 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/c54767b6-45db-4414-bb95-72619151a004 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task c54767b6-45db-4414-bb95-72619151a004 completed by agent papa-game in 2023ms (37 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 37 tokens, 4028ms
INFO:spl.executor:GENERATE chain done -> @steps_text (88 chars total)
[INFO] [arm=solver] decomposed into 7 step(s):


sin(x)|series
PREV|expand
PREV|expand
PREV|expand
PREV|expand
PREV|expand
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 72 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 127ms (0 LLM calls)
[INFO] [arm=solver][step 1/7] series(sin(x), x=0, deg≤5) = x**5/120 - x**3/6 + x
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 75 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 2/7] expand(x**5/120 - x**3/6 + x) = x**5/120 - x**3/6 + x
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 75 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[INFO] [arm=solver][step 3/7] expand(x**5/120 - x**3/6 + x) = x**5/120 - x**3/6 + x
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 75 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[INFO] [arm=solver][step 4/7] expand(x**5/120 - x**3/6 + x) = x**5/120 - x**3/6 + x
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 75 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[INFO] [arm=solver][step 5/7] expand(x**5/120 - x**3/6 + x) = x**5/120 - x**3/6 + x
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 75 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[INFO] [arm=solver][step 6/7] expand(x**5/120 - x**3/6 + x) = x**5/120 - x**3/6 + x
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 77 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 38ms (0 LLM calls)
[INFO] [arm=solver][step 7/7] simplify(x**5/120 - x**3/6 + x) = x**5/120 - x**3/6 + x
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 99ae3348-e77c-4fdc-bb56-ec60806cf49f submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/99ae3348-e77c-4fdc-bb56-ec60806cf49f "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/99ae3348-e77c-4fdc-bb56-ec60806cf49f "HTTP/1.1 200 OK"

Aborted!
```


## gemma3 (ollama) — backend=sage — solver=true — run 1

_Tier: T3 | Problem ID: `p015` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma3 \
   --param problem="solve the system of equations x + y = 5 and x - y = 1 for x and y" \
   --param hostname="mac-wens-Mac-mini.local" \
   --param backend=sage \
   --param enable_solver=true
```

```output
INFO:spl.registry:Registry: loaded 2 workflow(s) from cookbook/77_neurosymbolic/symbolic_math.spl
INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/77_neurosymbolic/sympolic_tools.spl
Registry: ['neurosymbolic_solver', 'solve_chain_step']
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
IPython kernel: enabled (name=python3, scope=session, timeout=60.0s)
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
Running workflow: neurosymbolic_solver(['problem', 'hostname', 'backend', 'enable_solver', 'model'])
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sage solver=true
[INFO] [arm=solver] Problem 'find the integral of sin(x) times cos(x), then simplify the result' — planning the chain (backend=sage) ...

Aborted!
```


## gemma3 (ollama) — backend=sage — solver=true — run 1

_Tier: T3 | Problem ID: `p016` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma3 \
   --param problem="find the eigenvalues of the 2 by 2 matrix with rows [1, 2] and [3, 4]" \
   --param hostname="mac-wens-Mac-mini.local" \
   --param backend=sage \
   --param enable_solver=true
```

```output
INFO:spl.registry:Registry: loaded 2 workflow(s) from cookbook/77_neurosymbolic/symbolic_math.spl
INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/77_neurosymbolic/sympolic_tools.spl
Registry: ['neurosymbolic_solver', 'solve_chain_step']
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
IPython kernel: enabled (name=python3, scope=session, timeout=60.0s)
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
Running workflow: neurosymbolic_solver(['problem', 'hostname', 'backend', 'enable_solver', 'model'])
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sage solver=true
[INFO] [arm=solver] Problem 'solve the system of equations x + y = 5 and x - y = 1 for x and y' — planning the chain (backend=sage) ...

Aborted!
```

INFO:spl.registry:Registry: loaded 2 workflow(s) from cookbook/77_neurosymbolic/symbolic_math.spl
INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/77_neurosymbolic/sympolic_tools.spl
Registry: ['neurosymbolic_solver', 'solve_chain_step']
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
IPython kernel: enabled (name=python3, scope=session, timeout=60.0s)
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
Running workflow: neurosymbolic_solver(['problem', 'hostname', 'backend', 'enable_solver', 'model'])
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sage solver=true
[INFO] [arm=solver] Problem 'integrate the square root of (4 minus x squared)' — planning the chain (backend=sage) ...

Aborted!
```


## gemma3 (ollama) — backend=sage — solver=true — run 1

_Tier: T4 | Problem ID: `p009` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma3 \
   --param problem="find the Laplace transform of exp(-2*t)" \
   --param hostname="mac-wens-Mac-mini.local" \
   --param backend=sage \
   --param enable_solver=true
```

```output

## gemma3 (ollama) — backend=sage — solver=true — run 1

_Tier: T4 | Problem ID: `p017` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma3 \
   --param problem="solve the ordinary differential equation y'(x) = y(x) with initial condition y(0) = 1" \
   --param hostname="mac-wens-Mac-mini.local" \
   --param backend=sage \
   --param enable_solver=true
```

```output
