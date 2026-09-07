# Recipe-77 Momagrid experiment run 20260620-215304

DB source: `exp-momagrid-20260620-215304`
Momagrid Hub: http://localhost:9000
Workers: 6


## gemma4:e2b (ollama) — backend=sympy — solver=true — run 1

_Tier: T0 | Problem ID: `p001` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma4:e2b \
   --param problem="differentiate x**4 - 2*x**2 + 1" \
   --param hostname="mac-wens-Mac-mini.local" \
   --param backend=sympy \
   --param enable_solver=true
```

```output

## gemma4:e2b (ollama) — backend=sympy — solver=true — run 1

_Tier: T0 | Problem ID: `p011` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma4:e2b \
   --param problem="simplify the rational expression (x**2 - 1) / (x - 1)" \
   --param hostname="mac-wens-Mac-mini.local" \
   --param backend=sympy \
   --param enable_solver=true
```

```output

## gemma4:e2b (ollama) — backend=sympy — solver=true — run 1

_Tier: T1 | Problem ID: `p002` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma4:e2b \
   --param problem="expand (x+1)**2, then factor the expanded form" \
   --param hostname="mac-wens-Mac-mini.local" \
   --param backend=sympy \
   --param enable_solver=true
```

```output

## gemma4:e2b (ollama) — backend=sympy — solver=true — run 1

_Tier: T1 | Problem ID: `p003` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma4:e2b \
   --param problem="differentiate 3*x**3-x, then factor if needed, finally solve for x" \
   --param hostname="mac-wens-Mac-mini.local" \
   --param backend=sympy \
   --param enable_solver=true
```

```output

## gemma4:e2b (ollama) — backend=sympy — solver=true — run 1

_Tier: T1 | Problem ID: `p004` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma4:e2b \
   --param problem="expand (x-2)**3, then differentiate the result, then simplify it, then factor that, then solve for x = 0" \
   --param hostname="mac-wens-Mac-mini.local" \
   --param backend=sympy \
   --param enable_solver=true
```

```output

## gemma4:e2b (ollama) — backend=sympy — solver=true — run 1

_Tier: T1 | Problem ID: `p012` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma4:e2b \
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
[INFO] [arm=solver] Problem 'expand (x+1)**2, then factor the expanded form' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task d53b2616-0a93-427a-be4b-f199a673447b submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/d53b2616-0a93-427a-be4b-f199a673447b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/d53b2616-0a93-427a-be4b-f199a673447b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/d53b2616-0a93-427a-be4b-f199a673447b "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task d53b2616-0a93-427a-be4b-f199a673447b completed by agent mac-wens-Mac-mini.local in 1963ms (16 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 16 tokens, 4049ms
INFO:spl.executor:GENERATE chain done -> @steps_text (30 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


(x + 1)**2|expand
PREV|factor


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 50 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 185ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] expand((x + 1)**2) = x**2 + 2*x + 1
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 46 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 2ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] factor(x**2 + 2*x + 1) = (x + 1)**2
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 2a9d5c5b-dfe4-43fd-af48-25490a24096b submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2a9d5c5b-dfe4-43fd-af48-25490a24096b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2a9d5c5b-dfe4-43fd-af48-25490a24096b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2a9d5c5b-dfe4-43fd-af48-25490a24096b "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 2a9d5c5b-dfe4-43fd-af48-25490a24096b completed by agent papa-game in 3209ms (122 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 122 tokens, 4032ms
INFO:spl.executor:GENERATE chain done -> @result (426 chars total)
INFO:spl.executor:RETURN: 426 chars | status=complete, arm=solver, backend=sympy, steps=2

Status:  complete
Output:  Okay, let’s break down this math problem! We need to see if we can factor a specific expression – namely, expanding and then factoring (x + 1)**2**. First, we expand that square:  (x + 1)**2 = x**2 + 2*x + 1. Next, we factor the resulting quadratic, which gives us (x + 1)**2**. This is because it’s a perfect square trinomial! It factors neatly back into its original form. Therefore, the final answer is simply **(x + 1)**2.
LLM calls: 2  Latency: 8270ms
Workers: mac-wens-Mac-mini.local, papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215305.md
```


## gemma4:e2b (ollama) — backend=sympy — solver=true — run 1

_Tier: T2 | Problem ID: `p005` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma4:e2b \
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
[INFO] [arm=solver] Problem 'simplify the rational expression (x**2 - 1) / (x - 1)' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 860044c1-b112-4d83-b14f-b586bd344aba submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/860044c1-b112-4d83-b14f-b586bd344aba "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/860044c1-b112-4d83-b14f-b586bd344aba "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/860044c1-b112-4d83-b14f-b586bd344aba "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 860044c1-b112-4d83-b14f-b586bd344aba completed by agent wengong in 1523ms (23 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 23 tokens, 4051ms
INFO:spl.executor:GENERATE chain done -> @steps_text (44 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


(x**2 - 1) / (x - 1)|simplify
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 44 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 217ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] simplify((x**2 - 1) / (x - 1)) = x + 1
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 29 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] simplify(x + 1) = x + 1
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task d541eab4-ef5e-4fd2-bbb1-862278c56a03 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/d541eab4-ef5e-4fd2-bbb1-862278c56a03 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/d541eab4-ef5e-4fd2-bbb1-862278c56a03 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/d541eab4-ef5e-4fd2-bbb1-862278c56a03 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task d541eab4-ef5e-4fd2-bbb1-862278c56a03 completed by agent wengong in 2810ms (118 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 118 tokens, 4022ms
INFO:spl.executor:GENERATE chain done -> @result (375 chars total)
INFO:spl.executor:RETURN: 375 chars | status=complete, arm=solver, backend=sympy, steps=2

Status:  complete
Output:  Okay, let's simplify the rational expression (x² - 1) / (x - 1). First, we recognize that x² - 1 is a difference of squares and can be factored into (x - 1)(x + 1).  Therefore, the expression becomes (x - 1)(x + 1) / (x - 1). We can then cancel out one factor of (x - 1) from the numerator and denominator, leaving us with x + 1. Finally, this simplified expression is x + 1.
LLM calls: 2  Latency: 8294ms
Workers: wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215305.md
```


## gemma4:e2b (ollama) — backend=sympy — solver=true — run 1

_Tier: T2 | Problem ID: `p006` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma4:e2b \
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
[INFO] [arm=solver] Problem 'differentiate x**4 - 2*x**2 + 1' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 5fdbda89-43cc-4f72-8b43-4bd5ca2fcf8d submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/5fdbda89-43cc-4f72-8b43-4bd5ca2fcf8d "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/5fdbda89-43cc-4f72-8b43-4bd5ca2fcf8d "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/5fdbda89-43cc-4f72-8b43-4bd5ca2fcf8d "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 5fdbda89-43cc-4f72-8b43-4bd5ca2fcf8d completed by agent mac-wens-Mac-mini.local in 1366ms (32 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 32 tokens, 4046ms
INFO:spl.executor:GENERATE chain done -> @steps_text (57 chars total)
[INFO] [arm=solver] decomposed into 4 step(s):


x**4 - 2*x**2 + 1|diff
PREV|diff
PREV|diff
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 51 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 184ms (0 LLM calls)
[INFO] [arm=solver][step 1/4] d/dx(x**4 - 2*x**2 + 1) = 4*x**3 - 4*x
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 44 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 3ms (0 LLM calls)
[INFO] [arm=solver][step 2/4] d/dx(4*x**3 - 4*x) = 12*x**2 - 4
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 29 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 3/4] d/dx(12*x**2 - 4) = 24*x
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 26 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 34ms (0 LLM calls)
[INFO] [arm=solver][step 4/4] simplify(24*x) = 24*x
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 9d2cbe22-c9b9-426e-a1e1-3aab6b95cbfd submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/9d2cbe22-c9b9-426e-a1e1-3aab6b95cbfd "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/9d2cbe22-c9b9-426e-a1e1-3aab6b95cbfd "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/9d2cbe22-c9b9-426e-a1e1-3aab6b95cbfd "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 9d2cbe22-c9b9-426e-a1e1-3aab6b95cbfd completed by agent mac-wens-Mac-mini.local in 2743ms (86 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 86 tokens, 4026ms
INFO:spl.executor:GENERATE chain done -> @result (300 chars total)
INFO:spl.executor:RETURN: 300 chars | status=complete, arm=solver, backend=sympy, steps=4

Status:  complete
Output:  Okay, let’s find the derivative of the function x⁴ - 2x² + 1. First, we differentiate the entire expression to get 4x³ - 4x. Next, we take the derivative again, which results in 12x². Then, differentiating that gives us 24x. Finally, simplifying this last result leaves us with our final answer: 24x.
LLM calls: 2  Latency: 8296ms
Workers: mac-wens-Mac-mini.local
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215305.md
```


## gemma4:e2b (ollama) — backend=sympy — solver=true — run 1

_Tier: T2 | Problem ID: `p013` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma4:e2b \
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
[INFO] [arm=solver] Problem 'differentiate 3*x**3-x, then factor if needed, finally solve for x' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 67e5b23c-3bbb-40aa-bbcb-7561cdc95846 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/67e5b23c-3bbb-40aa-bbcb-7561cdc95846 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/67e5b23c-3bbb-40aa-bbcb-7561cdc95846 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/67e5b23c-3bbb-40aa-bbcb-7561cdc95846 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 67e5b23c-3bbb-40aa-bbcb-7561cdc95846 completed by agent papa-game in 1443ms (21 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 21 tokens, 4045ms
INFO:spl.executor:GENERATE chain done -> @steps_text (39 chars total)
[INFO] [arm=solver] decomposed into 3 step(s):


3*x**3 - x|diff
PREV|factor
PREV|solve


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 40 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 195ms (0 LLM calls)
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
INFO:spl.adapters.momagrid:Task 2e0ffd40-0371-4cb6-a08c-5b5d00f82abf submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2e0ffd40-0371-4cb6-a08c-5b5d00f82abf "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2e0ffd40-0371-4cb6-a08c-5b5d00f82abf "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2e0ffd40-0371-4cb6-a08c-5b5d00f82abf "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2e0ffd40-0371-4cb6-a08c-5b5d00f82abf "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 2e0ffd40-0371-4cb6-a08c-5b5d00f82abf completed by agent wengong in 5001ms (133 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 133 tokens, 6035ms
INFO:spl.executor:GENERATE chain done -> @result (466 chars total)
INFO:spl.executor:RETURN: 466 chars | status=complete, arm=solver, backend=sympy, steps=3

Status:  complete
Output:  Okay, let's break down this problem! The student wanted us to find the derivative of the expression 3*x**3 - x and then solve for the values of x that make the resulting expression equal to zero. First, we differentiated the original expression to get 9*x**2 - 1. Next, we factored the quadratic expression 9*x**2 - 1 into (3*x - 1)*(3*x + 1). Finally, setting this factored form equal to zero allows us to solve for x, giving us two solutions: x = -1/3 and x = 1/3.
LLM calls: 2  Latency: 10278ms
Workers: papa-game, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215305.md
```


## gemma4:e2b (ollama) — backend=sympy — solver=true — run 1

_Tier: T2 | Problem ID: `p014` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma4:e2b \
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
[INFO] [arm=solver] Problem 'expand (x-2)**3, then differentiate the result, then simplify it, then factor that, then solve for x = 0' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task c00c99e0-d47b-4bf6-a1fd-eebcc10096da submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/c00c99e0-d47b-4bf6-a1fd-eebcc10096da "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/c00c99e0-d47b-4bf6-a1fd-eebcc10096da "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/c00c99e0-d47b-4bf6-a1fd-eebcc10096da "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task c00c99e0-d47b-4bf6-a1fd-eebcc10096da completed by agent papa-game in 2140ms (31 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 31 tokens, 4051ms
INFO:spl.executor:GENERATE chain done -> @steps_text (65 chars total)
[INFO] [arm=solver] decomposed into 5 step(s):


(x - 2)**3|expand
PREV|diff
PREV|simplify
PREV|factor
PREV|solve


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 70 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 185ms (0 LLM calls)
[INFO] [arm=solver][step 1/5] expand((x - 2)**3) = x**3 - 6*x**2 + 12*x - 8
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 70 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 3ms (0 LLM calls)
[INFO] [arm=solver][step 2/5] d/dx(x**3 - 6*x**2 + 12*x - 8) = 3*x**2 - 12*x + 12
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 68 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 35ms (0 LLM calls)
[INFO] [arm=solver][step 3/5] simplify(3*x**2 - 12*x + 12) = 3*x**2 - 12*x + 12
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 54 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 4/5] factor(3*x**2 - 12*x + 12) = 3*(x - 2)**2
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 34 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 2ms (0 LLM calls)
[INFO] [arm=solver][step 5/5] solve(3*(x - 2)**2 = 0) -> x = 2
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 65f644c0-faad-456f-b0c3-42d59d4eb30f submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/65f644c0-faad-456f-b0c3-42d59d4eb30f "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/65f644c0-faad-456f-b0c3-42d59d4eb30f "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/65f644c0-faad-456f-b0c3-42d59d4eb30f "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/65f644c0-faad-456f-b0c3-42d59d4eb30f "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/65f644c0-faad-456f-b0c3-42d59d4eb30f "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 65f644c0-faad-456f-b0c3-42d59d4eb30f completed by agent papa-game in 5959ms (148 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 148 tokens, 8036ms
INFO:spl.executor:GENERATE chain done -> @result (392 chars total)
INFO:spl.executor:RETURN: 392 chars | status=complete, arm=solver, backend=sympy, steps=5

Status:  complete
Output:  Okay, let's break down this problem! First, we expanded (x - 2)**3 to get x**3 - 6*x**2 + 12*x - 8. Then, we differentiated that expression, resulting in 3*x**2 - 12*x + 12.  Next, we simplified this derivative, which didn't change anything: 3*x**2 - 12*x + 12. We then factored it to get 3*(x - 2)**2, and finally, we solved the equation 3*(x - 2)**2 = 0 for x, revealing the solution x = 2.
LLM calls: 2  Latency: 12314ms
Workers: papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215305.md
```


## gemma4:e2b (ollama) — backend=sage — solver=true — run 1

_Tier: T3 | Problem ID: `p007` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma4:e2b \
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
[INFO] [arm=solver] Problem 'find the partial fraction decomposition of 1 / (x**2 - 1)' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task f29fe570-38ca-473b-8ba2-d47b52ab7d04 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f29fe570-38ca-473b-8ba2-d47b52ab7d04 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f29fe570-38ca-473b-8ba2-d47b52ab7d04 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f29fe570-38ca-473b-8ba2-d47b52ab7d04 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task f29fe570-38ca-473b-8ba2-d47b52ab7d04 completed by agent wengong in 1973ms (17 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 17 tokens, 4037ms
INFO:spl.executor:GENERATE chain done -> @steps_text (30 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


1/(x**2 - 1)|apart
PREV|apart


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 83 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 183ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] apart(1/(x**2 - 1)) = -1/(2*(x + 1)) + 1/(2*(x - 1))
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 101 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 3ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] apart(-1/(2*(x + 1)) + 1/(2*(x - 1))) = -1/(2*(x + 1)) + 1/(2*(x - 1))
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task a35d13d1-bfbc-4b12-a411-016512f12122 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a35d13d1-bfbc-4b12-a411-016512f12122 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a35d13d1-bfbc-4b12-a411-016512f12122 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a35d13d1-bfbc-4b12-a411-016512f12122 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a35d13d1-bfbc-4b12-a411-016512f12122 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a35d13d1-bfbc-4b12-a411-016512f12122 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a35d13d1-bfbc-4b12-a411-016512f12122 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task a35d13d1-bfbc-4b12-a411-016512f12122 completed by agent mac-wens-Mac-mini.local in 8943ms (219 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 219 tokens, 10069ms
INFO:spl.executor:GENERATE chain done -> @result (649 chars total)
INFO:spl.executor:RETURN: 649 chars | status=complete, arm=solver, backend=sympy, steps=2

Status:  complete
Output:  Okay, let's break down how to find the partial fraction decomposition of 1 / (x² - 1).  The problem asks us to split the complex fraction into simpler terms using linear factors. The symbolic engine first started by separating the original expression: `apart(1/(x**2 - 1)) = -1/(2*(x + 1)) + 1/(2*(x - 1))` which means we've broken down the denominator (x² - 1) into its factors, (x+1) and (x-1).  Next, it verified this result with `apart(-1/(2*(x + 1)) + 1/(2*(x - 1))) = -1/(2*(x + 1)) + 1/(2*(x - 1))` This just confirms the initial decomposition. Therefore, the partial fraction decomposition of 1 / (x² - 1) is  -1/(2*(x + 1)) + 1/(2*(x - 1)).
LLM calls: 2  Latency: 14294ms
Workers: mac-wens-Mac-mini.local, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215305.md
```


## gemma4:e2b (ollama) — backend=sage — solver=true — run 1

_Tier: T3 | Problem ID: `p008` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma4:e2b \
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
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sage solver=true
[INFO] [arm=solver] Problem 'integrate the square root of (4 minus x squared)' — planning the chain (backend=sage) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 9023ccce-364e-495b-a5a6-d19805400290 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/9023ccce-364e-495b-a5a6-d19805400290 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/9023ccce-364e-495b-a5a6-d19805400290 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/9023ccce-364e-495b-a5a6-d19805400290 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 9023ccce-364e-495b-a5a6-d19805400290 completed by agent wengong in 1334ms (33 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 33 tokens, 4029ms
INFO:spl.executor:GENERATE chain done -> @steps_text (70 chars total)
[INFO] [arm=solver] decomposed into 4 step(s):


√(4 - x**2)|integrate
PREV|simplify
PREV|trigsimp
PREV|acos(x/2)|acos


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 110 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1814ms (0 LLM calls)
[INFO] [arm=solver][step 1/4] integral of √(4 - x**2) dx = 1/2*sqrt(-x^2 + 4)*x + 2*arcsin(1/2*x) + C
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 128 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 12ms (0 LLM calls)
[INFO] [arm=solver][step 2/4] simplify(1/2*sqrt(-x^2 + 4)*x + 2*arcsin(1/2*x)) = 1/2*sqrt(-x^2 + 4)*x + 2*arcsin(1/2*x)
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 128 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 4ms (0 LLM calls)
[INFO] [arm=solver][step 3/4] trigsimp(1/2*sqrt(-x^2 + 4)*x + 2*arcsin(1/2*x)) = 1/2*sqrt(-x^2 + 4)*x + 2*arcsin(1/2*x)
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 63 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[ERROR] [arm=solver] SOLVER FAILURE at step 4/4: unknown operation 'acos(x/2)' — not in Sage kernel
INFO:spl.executor:RETURN: 394 chars | status=solver_error, arm=solver, backend=sage, steps=4

Status:  complete
Output:  [SOLVER FAILURE] Step 4/4 could not be computed: unknown operation 'acos(x/2)' — not in Sage kernel
Verified chain up to this point:
1. integral of √(4 - x**2) dx = 1/2*sqrt(-x^2 + 4)*x + 2*arcsin(1/2*x) + C
2. simplify(1/2*sqrt(-x^2 + 4)*x + 2*arcsin(1/2*x)) = 1/2*sqrt(-x^2 + 4)*x + 2*arcsin(1/2*x)
3. trigsimp(1/2*sqrt(-x^2 + 4)*x + 2*arcsin(1/2*x)) = 1/2*sqrt(-x^2 + 4)*x + 2*arcsin(1/2*x)

LLM calls: 1  Latency: 5861ms
Workers: wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215318.md
```


## gemma4:e2b (ollama) — backend=sage — solver=true — run 1

_Tier: T3 | Problem ID: `p015` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma4:e2b \
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
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sympy solver=true
[INFO] [arm=solver] Problem 'differentiate exp(x) and simplify it if necessary' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 413a6d59-12fe-4ec3-9353-191f42d6b14a submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/413a6d59-12fe-4ec3-9353-191f42d6b14a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/413a6d59-12fe-4ec3-9353-191f42d6b14a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/413a6d59-12fe-4ec3-9353-191f42d6b14a "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 413a6d59-12fe-4ec3-9353-191f42d6b14a completed by agent wengong in 1098ms (12 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 12 tokens, 4034ms
INFO:spl.executor:GENERATE chain done -> @steps_text (26 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


exp(x)|diff
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 28 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 142ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] d/dx(exp(x)) = exp(x)
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 32 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 46ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] simplify(exp(x)) = exp(x)
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 69e53eae-2c15-4db2-b035-0f34af7a9a2f submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/69e53eae-2c15-4db2-b035-0f34af7a9a2f "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/69e53eae-2c15-4db2-b035-0f34af7a9a2f "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/69e53eae-2c15-4db2-b035-0f34af7a9a2f "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/69e53eae-2c15-4db2-b035-0f34af7a9a2f "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 69e53eae-2c15-4db2-b035-0f34af7a9a2f completed by agent papa-game in 2970ms (112 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 112 tokens, 6028ms
INFO:spl.executor:GENERATE chain done -> @result (430 chars total)
INFO:spl.executor:RETURN: 428 chars | status=complete, arm=solver, backend=sympy, steps=2

Status:  complete
Output:  Okay, let’s break down this problem! We need to find the derivative of the exponential function `exp(x)` and then simplify it. First, we take the derivative with respect to `x`, which results in `exp(x)`. Then, since `exp(x)` doesn't have any complex terms within it, the derivative remains simply as `exp(x)`. Therefore, the simplified result of the derivative is `exp(x)`. This means that the derivative of `exp(x)` is itself!
LLM calls: 2  Latency: 10251ms
Workers: papa-game, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215314.md
```


## gemma4:e2b (ollama) — backend=sage — solver=true — run 1

_Tier: T3 | Problem ID: `p016` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma4:e2b \
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
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sympy solver=true
[INFO] [arm=solver] Problem 'simplify sin(x)**2 + cos(x)**2 using trigonometric identities' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task fa1ce466-ec4c-4bb6-af7b-784e739a7ed1 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/fa1ce466-ec4c-4bb6-af7b-784e739a7ed1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/fa1ce466-ec4c-4bb6-af7b-784e739a7ed1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/fa1ce466-ec4c-4bb6-af7b-784e739a7ed1 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task fa1ce466-ec4c-4bb6-af7b-784e739a7ed1 completed by agent papa-game in 1015ms (22 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 22 tokens, 4043ms
INFO:spl.executor:GENERATE chain done -> @steps_text (45 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


sin(x)**2 + cos(x)**2|trigsimp
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 37 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 115ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] trigsimp(sin(x)**2 + cos(x)**2) = 1
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 17 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] simplify(1) = 1
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task f6e3cd07-25ce-4825-83af-624d0382bdce submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f6e3cd07-25ce-4825-83af-624d0382bdce "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f6e3cd07-25ce-4825-83af-624d0382bdce "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f6e3cd07-25ce-4825-83af-624d0382bdce "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f6e3cd07-25ce-4825-83af-624d0382bdce "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task f6e3cd07-25ce-4825-83af-624d0382bdce completed by agent wengong in 2899ms (111 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 111 tokens, 6027ms
INFO:spl.executor:GENERATE chain done -> @result (420 chars total)
INFO:spl.executor:RETURN: 420 chars | status=complete, arm=solver, backend=sympy, steps=2

Status:  complete
Output:  Okay, let's simplify the expression sin(x)² + cos(x)². This problem asks us to use trigonometric identities to find a simpler form for this sum of squares. The symbolic math engine first used `trigsimp` to reduce the expression directly to 1: sin(x)² + cos(x) = 1.  Then, it further simplified this result using `simplify`, confirming that the value is indeed 1. Therefore, the simplified form of sin(x)² + cos(x)² is 1.
LLM calls: 2  Latency: 10186ms
Workers: papa-game, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215316.md
```


## gemma4:e2b (ollama) — backend=sage — solver=true — run 1

_Tier: T4 | Problem ID: `p009` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma4:e2b \
   --param problem="find the Laplace transform of exp(-2*t)" \
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
[INFO] [arm=solver] Problem 'find the limit of sin(x) divided by x as x approaches 0' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 20508d50-5206-4661-b571-5c9d72c596aa submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/20508d50-5206-4661-b571-5c9d72c596aa "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/20508d50-5206-4661-b571-5c9d72c596aa "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/20508d50-5206-4661-b571-5c9d72c596aa "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 20508d50-5206-4661-b571-5c9d72c596aa completed by agent papa-game in 1332ms (19 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 19 tokens, 4030ms
INFO:spl.executor:GENERATE chain done -> @steps_text (34 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


sin(x)/x|limit(x,0)
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 27 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 145ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] limit(sin(x)/x, x->0) = 1
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 17 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] simplify(1) = 1
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 02d556fa-616a-4a95-8ade-1644f14de190 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/02d556fa-616a-4a95-8ade-1644f14de190 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/02d556fa-616a-4a95-8ade-1644f14de190 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/02d556fa-616a-4a95-8ade-1644f14de190 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/02d556fa-616a-4a95-8ade-1644f14de190 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/02d556fa-616a-4a95-8ade-1644f14de190 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 02d556fa-616a-4a95-8ade-1644f14de190 completed by agent papa-game in 4997ms (97 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 97 tokens, 8036ms
INFO:spl.executor:GENERATE chain done -> @result (373 chars total)
INFO:spl.executor:RETURN: 373 chars | status=complete, arm=solver, backend=sympy, steps=2

Status:  complete
Output:  Okay, let's tackle this limit problem! The question asks us to find the value that sin(x) / x approaches as x gets closer and closer to zero.  The symbolic engine first determined the limit of sin(x)/x as x approaches 0 is equal to 1. Next, it simplified this result, confirming that the answer remains 1. Therefore, the limit of sin(x) divided by x as x approaches 0 is 1.
LLM calls: 2  Latency: 12213ms
Workers: papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215314.md
```


## gemma4:e2b (ollama) — backend=sage — solver=true — run 1

_Tier: T4 | Problem ID: `p017` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma4:e2b \
   --param problem="solve the ordinary differential equation y'(x) = y(x) with initial condition y(0) = 1" \
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
INFO:spl.adapters.momagrid:Task 74a8a712-67d1-4664-afe4-280648547c8c submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/74a8a712-67d1-4664-afe4-280648547c8c "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/74a8a712-67d1-4664-afe4-280648547c8c "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/74a8a712-67d1-4664-afe4-280648547c8c "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/74a8a712-67d1-4664-afe4-280648547c8c "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 74a8a712-67d1-4664-afe4-280648547c8c completed by agent mac-wens-Mac-mini.local in 4068ms (32 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 32 tokens, 6036ms
INFO:spl.executor:GENERATE chain done -> @steps_text (58 chars total)
[INFO] [arm=solver] decomposed into 7 step(s):


sin(x)|series
PREV|
PREV|
PREV|
PREV|
PREV|
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 72 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 117ms (0 LLM calls)
[INFO] [arm=solver][step 1/7] series(sin(x), x=0, deg≤5) = x**5/120 - x**3/6 + x
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 58 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[INFO] [arm=solver][step 2/7] x**5/120 - x**3/6 + x (pass-through)
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 58 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[INFO] [arm=solver][step 3/7] x**5/120 - x**3/6 + x (pass-through)
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 58 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[INFO] [arm=solver][step 4/7] x**5/120 - x**3/6 + x (pass-through)
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 58 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[INFO] [arm=solver][step 5/7] x**5/120 - x**3/6 + x (pass-through)
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 58 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[INFO] [arm=solver][step 6/7] x**5/120 - x**3/6 + x (pass-through)
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 77 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 36ms (0 LLM calls)
[INFO] [arm=solver][step 7/7] simplify(x**5/120 - x**3/6 + x) = x**5/120 - x**3/6 + x
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task ac624463-73b4-43b8-b4b7-f41ea96f4c84 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ac624463-73b4-43b8-b4b7-f41ea96f4c84 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ac624463-73b4-43b8-b4b7-f41ea96f4c84 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ac624463-73b4-43b8-b4b7-f41ea96f4c84 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ac624463-73b4-43b8-b4b7-f41ea96f4c84 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ac624463-73b4-43b8-b4b7-f41ea96f4c84 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task ac624463-73b4-43b8-b4b7-f41ea96f4c84 completed by agent mac-wens-Mac-mini.local in 5083ms (113 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 113 tokens, 8034ms
INFO:spl.executor:GENERATE chain done -> @result (451 chars total)
INFO:spl.executor:RETURN: 449 chars | status=complete, arm=solver, backend=sympy, steps=7

Status:  complete
Output:  Okay, let's expand the sine function, sin(x), using its Taylor series around x = 0, and we’ll keep terms up to a degree of 5. The engine first calculated the Taylor series as  x⁵/120 - x³/6 + x. This result then passed through unchanged in subsequent steps, repeated five times – essentially confirming the initial series expansion. After this repetition, the expression was simplified, arriving at the final exact representation: x⁵/120 - x³/6 + x.
LLM calls: 2  Latency: 14225ms
Workers: mac-wens-Mac-mini.local
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215314.md
```


## gemma4:e2b (ollama) — backend=sage — solver=true — run 1

_Tier: T4 | Problem ID: `p018` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma4:e2b \
   --param problem="compute the symbolic sum of 1 over n squared from n equals 1 to infinity" \
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
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 0b241e89-268b-4ca0-9039-fea558f79924 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/0b241e89-268b-4ca0-9039-fea558f79924 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/0b241e89-268b-4ca0-9039-fea558f79924 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/0b241e89-268b-4ca0-9039-fea558f79924 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 0b241e89-268b-4ca0-9039-fea558f79924 completed by agent wengong in 1422ms (35 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 35 tokens, 4039ms
INFO:spl.executor:GENERATE chain done -> @steps_text (66 chars total)
[INFO] [arm=solver] decomposed into 4 step(s):


x + y = 5|solve
PREV - y = -1|solve
PREV - x = 4|solve
PREV|solve


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 41 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1793ms (0 LLM calls)
[INFO] [arm=solver][step 1/4] solve(x + y = 5 = 0) -> x = -y + 5
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 41 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 2/4] solve((-y + 5) - y = -1 = 0) -> x = []
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 110 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[ERROR] [arm=solver] SOLVER FAILURE at step 3/4: ([]) - x = 4: unsupported operand type(s) for -: 'list' and 'sage.symbolic.expression.Expression'
INFO:spl.executor:RETURN: 260 chars | status=solver_error, arm=solver, backend=sage, steps=3

Status:  complete
Output:  [SOLVER FAILURE] Step 3/4 could not be computed: ([]) - x = 4: unsupported operand type(s) for -: 'list' and 'sage.symbolic.expression.Expression'
Verified chain up to this point:
1. solve(x + y = 5 = 0) -> x = -y + 5
2. solve((-y + 5) - y = -1 = 0) -> x = []

LLM calls: 1  Latency: 5834ms
Workers: wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215324.md
```


## gemma4:e2b (ollama) — backend=sage — solver=true — run 1

_Tier: T4 | Problem ID: `p019` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma4:e2b \
   --param problem="find all roots of x**4 - 1 and express each root in simplified form" \
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
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 70ef7648-c4c1-4f3d-b98e-8b99176926ba submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/70ef7648-c4c1-4f3d-b98e-8b99176926ba "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/70ef7648-c4c1-4f3d-b98e-8b99176926ba "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/70ef7648-c4c1-4f3d-b98e-8b99176926ba "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 70ef7648-c4c1-4f3d-b98e-8b99176926ba completed by agent mac-wens-Mac-mini.local in 1089ms (21 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 21 tokens, 4033ms
INFO:spl.executor:GENERATE chain done -> @steps_text (52 chars total)
[INFO] [arm=solver] decomposed into 3 step(s):


sin(x)*cos(x)|integrate
PREV|simplify
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 62 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1902ms (0 LLM calls)
[INFO] [arm=solver][step 1/3] integral of sin(x)*cos(x) dx = -1/2*cos(x)^2 + C
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 53 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 6ms (0 LLM calls)
[INFO] [arm=solver][step 2/3] simplify(-1/2*cos(x)^2) = -1/2*cos(x)^2
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 53 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 2ms (0 LLM calls)
[INFO] [arm=solver][step 3/3] simplify(-1/2*cos(x)^2) = -1/2*cos(x)^2
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task bdf029af-e87b-45c2-9f4a-50ab4204d4d5 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/bdf029af-e87b-45c2-9f4a-50ab4204d4d5 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/bdf029af-e87b-45c2-9f4a-50ab4204d4d5 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/bdf029af-e87b-45c2-9f4a-50ab4204d4d5 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/bdf029af-e87b-45c2-9f4a-50ab4204d4d5 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task bdf029af-e87b-45c2-9f4a-50ab4204d4d5 completed by agent papa-game in 3022ms (108 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 108 tokens, 6044ms
INFO:spl.executor:GENERATE chain done -> @result (324 chars total)
INFO:spl.executor:RETURN: 324 chars | status=complete, arm=solver, backend=sage, steps=3

Status:  complete
Output:  Okay, let's find the integral of sin(x) * cos(x) and simplify it! First, we use a u-substitution to evaluate the integral:  integral of sin(x)*cos(x) dx = -1/2*cos(x)^2 + C. Then, we simply this expression by leaving -1/2*cos(x)^2 as is.  Finally, after further simplification, our final answer remains at -1/2*cos(x)^2 + C.
LLM calls: 2  Latency: 11988ms
Workers: mac-wens-Mac-mini.local, papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215320.md
```


## gemma4:e2b (ollama) — backend=sage — solver=true — run 1

_Tier: T5 | Problem ID: `p010` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma4:e2b \
   --param problem="find the general solution to the second order ODE y''(x) - 3*y'(x) + 2*y(x) = 0" \
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
[INFO] [arm=solver] Problem 'find the eigenvalues of the 2 by 2 matrix with rows [1, 2] and [3, 4]' — planning the chain (backend=sage) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 472322c8-e179-4923-8e27-9c7846275399 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/472322c8-e179-4923-8e27-9c7846275399 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/472322c8-e179-4923-8e27-9c7846275399 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/472322c8-e179-4923-8e27-9c7846275399 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 472322c8-e179-4923-8e27-9c7846275399 completed by agent papa-game in 1259ms (16 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 16 tokens, 4033ms
INFO:spl.executor:GENERATE chain done -> @steps_text (28 chars total)
[INFO] [arm=solver] decomposed into 1 step(s):


[[1, 2], [3, 4]]|eigenvalues


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 115 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1861ms (0 LLM calls)
[INFO] [arm=solver][step 1/1] eigenvalues([[1, 2], [3, 4]]) = [-1/2*sqrt(33) + 5/2, 1/2*sqrt(33) + 5/2]
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 54166855-2573-4be0-ad2d-aa0929948f78 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/54166855-2573-4be0-ad2d-aa0929948f78 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/54166855-2573-4be0-ad2d-aa0929948f78 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/54166855-2573-4be0-ad2d-aa0929948f78 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/54166855-2573-4be0-ad2d-aa0929948f78 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 54166855-2573-4be0-ad2d-aa0929948f78 completed by agent wengong in 3326ms (157 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 157 tokens, 6028ms
INFO:spl.executor:GENERATE chain done -> @result (451 chars total)
INFO:spl.executor:RETURN: 451 chars | status=complete, arm=solver, backend=sage, steps=1

Status:  complete
Output:  Okay, let's find the eigenvalues of the 2x2 matrix with rows [1, 2] and [3, 4]. The symbolic math engine calculated these eigenvalues using a specific formula. First, it determined that the eigenvalues are -1/2*sqrt(33) + 5/2 and 1/2*sqrt(33) + 5/2. These are the two distinct values that satisfy the equation λ² - trace(A)λ + det(A) = 0, where A is our matrix.  Therefore, the eigenvalues of the matrix are -1/2*sqrt(33) + 5/2 and 1/2*sqrt(33) + 5/2.
LLM calls: 2  Latency: 11923ms
Workers: papa-game, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215325.md
```


## gemma4:e2b (ollama) — backend=sage — solver=true — run 1

_Tier: T5 | Problem ID: `p020` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma4:e2b \
   --param problem="compute the inverse Laplace transform of s / (s**2 + 4), then verify by taking the Laplace transform of the result" \
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
[INFO] [arm=solver] Problem 'find the Laplace transform of exp(-2*t)' — planning the chain (backend=sage) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 3a5f5729-36bb-4233-bcfb-ccbcc2473fc9 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/3a5f5729-36bb-4233-bcfb-ccbcc2473fc9 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/3a5f5729-36bb-4233-bcfb-ccbcc2473fc9 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/3a5f5729-36bb-4233-bcfb-ccbcc2473fc9 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 3a5f5729-36bb-4233-bcfb-ccbcc2473fc9 completed by agent mac-wens-Mac-mini.local in 892ms (15 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 15 tokens, 4030ms
INFO:spl.executor:GENERATE chain done -> @steps_text (30 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


exp(-2*t)|laplace
PREV|laplace


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 50 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1976ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] laplace_transform(exp(-2*t)) = 1/(s + 2)
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 58 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] laplace_transform(1/(s + 2)) = 1/((s + 2)*s)
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 347109f0-dfad-4888-baed-42235bbf6c1c submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/347109f0-dfad-4888-baed-42235bbf6c1c "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/347109f0-dfad-4888-baed-42235bbf6c1c "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/347109f0-dfad-4888-baed-42235bbf6c1c "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/347109f0-dfad-4888-baed-42235bbf6c1c "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 347109f0-dfad-4888-baed-42235bbf6c1c completed by agent wengong in 3296ms (119 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 119 tokens, 6027ms
INFO:spl.executor:GENERATE chain done -> @result (438 chars total)
INFO:spl.executor:RETURN: 438 chars | status=complete, arm=solver, backend=sage, steps=2

Status:  complete
Output:  Okay, let's find the Laplace transform of the function exp(-2t). The Laplace transform converts a time-domain function into one expressed in terms of complex frequencies. Starting with exp(-2t), we first apply the standard Laplace transform rule, resulting in 1/(s + 2).  Then, we simplify 1/(s+2) by multiplying both numerator and denominator by 's', yielding 1/((s + 2)*s). Therefore, the Laplace transform of exp(-2t) is 1/((s + 2)*s).
LLM calls: 2  Latency: 12035ms
Workers: mac-wens-Mac-mini.local, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215326.md
```

INFO:spl.registry:Registry: loaded 2 workflow(s) from cookbook/77_neurosymbolic/symbolic_math.spl
INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/77_neurosymbolic/sympolic_tools.spl
Registry: ['neurosymbolic_solver', 'solve_chain_step']
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
IPython kernel: enabled (name=python3, scope=session, timeout=60.0s)
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
Running workflow: neurosymbolic_solver(['problem', 'hostname', 'backend', 'enable_solver', 'model'])
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sage solver=true
[INFO] [arm=solver] Problem 'solve the ordinary differential equation y'(x) = y(x) with initial condition y(0) = 1' — planning the chain (backend=sage) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 6cd61bb7-e1e7-4643-882d-c2e1358ea4d9 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/6cd61bb7-e1e7-4643-882d-c2e1358ea4d9 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/6cd61bb7-e1e7-4643-882d-c2e1358ea4d9 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/6cd61bb7-e1e7-4643-882d-c2e1358ea4d9 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 6cd61bb7-e1e7-4643-882d-c2e1358ea4d9 completed by agent wengong in 1124ms (25 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 25 tokens, 4029ms
INFO:spl.executor:GENERATE chain done -> @steps_text (45 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


y(x).diff(x) - y(x)|ode_solve
PREV|ode_solve


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 64 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1683ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] dsolve(y(x).diff(x) - y(x) = 0) -> Eq(y(x), C1*exp(x))
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 51 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] C1*exp(x) (already solved — pass-through)
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task eda43ec9-389c-409b-8310-6c57996cc180 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/eda43ec9-389c-409b-8310-6c57996cc180 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/eda43ec9-389c-409b-8310-6c57996cc180 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/eda43ec9-389c-409b-8310-6c57996cc180 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/eda43ec9-389c-409b-8310-6c57996cc180 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/eda43ec9-389c-409b-8310-6c57996cc180 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task eda43ec9-389c-409b-8310-6c57996cc180 completed by agent mac-wens-Mac-mini.local in 4805ms (157 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 157 tokens, 8059ms
INFO:spl.executor:GENERATE chain done -> @result (602 chars total)
INFO:spl.executor:RETURN: 602 chars | status=complete, arm=solver, backend=sage, steps=2

Status:  complete
Output:  Okay, let’s solve this differential equation! The problem asks us to find a function y(x) whose derivative is equal to itself, with the starting value of y(0) being 1.  The symbolic engine first solved the differential equation `y'(x) = y(x)` and determined that the general solution is `y(x) = C1 * exp(x)`, where C1 is an arbitrary constant. This represents all possible solutions to the equation. Using the initial condition `y(0) = 1`, we can find the value of C1, which results in `C1 = 1`. Therefore, the solution to the differential equation with the given initial condition is  `y(x) = exp(x)`.
LLM calls: 2  Latency: 13772ms
Workers: mac-wens-Mac-mini.local, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215327.md
```

INFO:spl.registry:Registry: loaded 2 workflow(s) from cookbook/77_neurosymbolic/symbolic_math.spl
INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/77_neurosymbolic/sympolic_tools.spl
Registry: ['neurosymbolic_solver', 'solve_chain_step']
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
IPython kernel: enabled (name=python3, scope=session, timeout=60.0s)
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
Running workflow: neurosymbolic_solver(['problem', 'hostname', 'backend', 'enable_solver', 'model'])
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sage solver=true
[INFO] [arm=solver] Problem 'compute the symbolic sum of 1 over n squared from n equals 1 to infinity' — planning the chain (backend=sage) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task a046ef50-266e-410f-a386-de10d165842c submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a046ef50-266e-410f-a386-de10d165842c "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a046ef50-266e-410f-a386-de10d165842c "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a046ef50-266e-410f-a386-de10d165842c "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task a046ef50-266e-410f-a386-de10d165842c completed by agent wengong in 1086ms (16 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 16 tokens, 4029ms
INFO:spl.executor:GENERATE chain done -> @steps_text (24 chars total)
[INFO] [arm=solver] decomposed into 1 step(s):


1/n**2|summation(n,1,oo)


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 47 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1783ms (0 LLM calls)
[INFO] [arm=solver][step 1/1] sum(1/n**2, n=1..+Infinity) = 1/6*pi^2
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 029d17d2-b608-4b1a-92f4-96312240a602 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/029d17d2-b608-4b1a-92f4-96312240a602 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/029d17d2-b608-4b1a-92f4-96312240a602 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/029d17d2-b608-4b1a-92f4-96312240a602 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/029d17d2-b608-4b1a-92f4-96312240a602 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 029d17d2-b608-4b1a-92f4-96312240a602 completed by agent papa-game in 3072ms (125 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 125 tokens, 6034ms
INFO:spl.executor:GENERATE chain done -> @result (449 chars total)
INFO:spl.executor:RETURN: 449 chars | status=complete, arm=solver, backend=sage, steps=1

Status:  complete
Output:  Okay, let’s break down this calculation! The problem asks us to find the value of the infinite sum: 1 over n squared, starting with n equals 1 and going on forever.  The engine first simplified the entire sum to just 1/6 * pi^2. Then it evaluated this expression, resulting in 1/6 * pi^2 = 1/6 * (3.14159...)^2. This calculation yields a specific numerical value. Therefore, the symbolic sum of 1 over n squared from n equals 1 to infinity is π²/6 .
LLM calls: 2  Latency: 11847ms
Workers: papa-game, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215329.md
```

INFO:spl.registry:Registry: loaded 2 workflow(s) from cookbook/77_neurosymbolic/symbolic_math.spl
INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/77_neurosymbolic/sympolic_tools.spl
Registry: ['neurosymbolic_solver', 'solve_chain_step']
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
IPython kernel: enabled (name=python3, scope=session, timeout=60.0s)
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
Running workflow: neurosymbolic_solver(['problem', 'hostname', 'backend', 'enable_solver', 'model'])
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sage solver=true
[INFO] [arm=solver] Problem 'find all roots of x**4 - 1 and express each root in simplified form' — planning the chain (backend=sage) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task c4c9dcd8-572d-4680-9cee-9171fa75a458 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/c4c9dcd8-572d-4680-9cee-9171fa75a458 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/c4c9dcd8-572d-4680-9cee-9171fa75a458 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/c4c9dcd8-572d-4680-9cee-9171fa75a458 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task c4c9dcd8-572d-4680-9cee-9171fa75a458 completed by agent mac-wens-Mac-mini.local in 1352ms (30 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 30 tokens, 4032ms
INFO:spl.executor:GENERATE chain done -> @steps_text (71 chars total)
[INFO] [arm=solver] decomposed into 5 step(s):


x**4 - 1|solve
PREV|simplify
PREV|simplify
PREV|simplify
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 56 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1836ms (0 LLM calls)
[INFO] [arm=solver][step 1/5] solve(x**4 - 1 = 0) -> x = [I, -1, -I, 1]
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 56 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[INFO] [arm=solver][step 2/5] simplify([I, -1, -I, 1]) = [I, -1, -I, 1]
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 56 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[INFO] [arm=solver][step 3/5] simplify([I, -1, -I, 1]) = [I, -1, -I, 1]
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 56 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[INFO] [arm=solver][step 4/5] simplify([I, -1, -I, 1]) = [I, -1, -I, 1]
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 56 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[INFO] [arm=solver][step 5/5] simplify([I, -1, -I, 1]) = [I, -1, -I, 1]
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task f1af8e45-5375-416a-bae8-34eb886e59c4 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f1af8e45-5375-416a-bae8-34eb886e59c4 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f1af8e45-5375-416a-bae8-34eb886e59c4 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f1af8e45-5375-416a-bae8-34eb886e59c4 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f1af8e45-5375-416a-bae8-34eb886e59c4 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task f1af8e45-5375-416a-bae8-34eb886e59c4 completed by agent wengong in 3175ms (128 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 128 tokens, 6034ms
INFO:spl.executor:GENERATE chain done -> @result (471 chars total)
INFO:spl.executor:RETURN: 471 chars | status=complete, arm=solver, backend=sage, steps=5

Status:  complete
Output:  The student was asked to find all the solutions (roots) of the equation x⁴ - 1 = 0 and express them in their simplest form. The symbolic math engine first solved this equation, resulting in the roots: x = [I, -1, -I, 1].  Next, it simplified this list of roots, which remained unchanged at [I, -1, -I, 1].  The simplification process continued identically, ensuring the root representation stayed consistent.  Therefore, the solutions to x⁴ - 1 = 0 are: i, -1, -i, and 1.
LLM calls: 2  Latency: 11904ms
Workers: mac-wens-Mac-mini.local, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215331.md
```

INFO:spl.registry:Registry: loaded 2 workflow(s) from cookbook/77_neurosymbolic/symbolic_math.spl
INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/77_neurosymbolic/sympolic_tools.spl
Registry: ['neurosymbolic_solver', 'solve_chain_step']
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
IPython kernel: enabled (name=python3, scope=session, timeout=60.0s)
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
Running workflow: neurosymbolic_solver(['problem', 'hostname', 'backend', 'enable_solver', 'model'])
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sage solver=true
[INFO] [arm=solver] Problem 'find the general solution to the second order ODE y''(x) - 3*y'(x) + 2*y(x) = 0' — planning the chain (backend=sage) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 1fc61e81-7ab8-4ebf-8dfc-94e3649b8f91 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1fc61e81-7ab8-4ebf-8dfc-94e3649b8f91 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1fc61e81-7ab8-4ebf-8dfc-94e3649b8f91 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1fc61e81-7ab8-4ebf-8dfc-94e3649b8f91 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 1fc61e81-7ab8-4ebf-8dfc-94e3649b8f91 completed by agent papa-game in 1683ms (42 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 42 tokens, 4041ms
INFO:spl.executor:GENERATE chain done -> @steps_text (66 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


y(x).diff(x,2) - 3*y(x).diff(x) + 2*y(x)|ode_solve
PREV|ode_solve


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 113 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1721ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] dsolve(y(x).diff(x,2) - 3*y(x).diff(x) + 2*y(x) = 0) -> Eq(y(x), (C1 + C2*exp(x))*exp(x))
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 79 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] (C1 + C2*exp(x))*exp(x) (already solved — pass-through)
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 30e45c83-fa35-4354-bf5e-771de2920190 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/30e45c83-fa35-4354-bf5e-771de2920190 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/30e45c83-fa35-4354-bf5e-771de2920190 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/30e45c83-fa35-4354-bf5e-771de2920190 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/30e45c83-fa35-4354-bf5e-771de2920190 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 30e45c83-fa35-4354-bf5e-771de2920190 completed by agent papa-game in 3729ms (157 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 157 tokens, 6041ms
INFO:spl.executor:GENERATE chain done -> @result (631 chars total)
INFO:spl.executor:RETURN: 631 chars | status=complete, arm=solver, backend=sage, steps=2

Status:  complete
Output:  Okay, let's solve this second-order ordinary differential equation: y''(x) - 3*y'(x) + 2*y(x) = 0. The symbolic math engine first recognized the equation and found a general solution expressed with two arbitrary constants, C1 and C2, combined with exponential functions:  y(x) = (C1 + C2*exp(x))*exp(x). This initial step involved solving the characteristic equation of the associated second-order linear ODE. The engine then simply passed through this already computed solution without further steps because it was fully solved. Therefore, the general solution to the given differential equation is y(x) = (C1 + C2*exp(x))*exp(x).
LLM calls: 2  Latency: 11804ms
Workers: papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215332.md
```

INFO:spl.registry:Registry: loaded 2 workflow(s) from cookbook/77_neurosymbolic/symbolic_math.spl
INFO:spl.registry:Registry: loaded 0 workflow(s) from cookbook/77_neurosymbolic/sympolic_tools.spl
Registry: ['neurosymbolic_solver', 'solve_chain_step']
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
IPython kernel: enabled (name=python3, scope=session, timeout=60.0s)
INFO:spl.executor:IPython kernel registered: CALL run_python(@code) INTO @result
Running workflow: neurosymbolic_solver(['problem', 'hostname', 'backend', 'enable_solver', 'model'])
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sage solver=true
[INFO] [arm=solver] Problem 'compute the inverse Laplace transform of s / (s**2 + 4), then verify by taking the Laplace transform of the result' — planning the chain (backend=sage) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 805bb39f-0f01-401c-bf22-9e81de832f30 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/805bb39f-0f01-401c-bf22-9e81de832f30 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/805bb39f-0f01-401c-bf22-9e81de832f30 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/805bb39f-0f01-401c-bf22-9e81de832f30 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 805bb39f-0f01-401c-bf22-9e81de832f30 completed by agent papa-game in 1959ms (22 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 22 tokens, 4063ms
INFO:spl.executor:GENERATE chain done -> @steps_text (44 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


s / (s**2 + 4)|inverse_laplace
PREV|laplace


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 61 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1823ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] inverse_laplace_transform(s / (s**2 + 4)) = cos(2*t)
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 53 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] laplace_transform(cos(2*t)) = s/(s^2 + 4)
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 55079c56-5f09-476b-b46a-d346e6e8688e submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/55079c56-5f09-476b-b46a-d346e6e8688e "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/55079c56-5f09-476b-b46a-d346e6e8688e "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/55079c56-5f09-476b-b46a-d346e6e8688e "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 55079c56-5f09-476b-b46a-d346e6e8688e completed by agent mac-wens-Mac-mini.local in 3643ms (107 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 107 tokens, 4035ms
INFO:spl.executor:GENERATE chain done -> @result (371 chars total)
INFO:spl.executor:RETURN: 371 chars | status=complete, arm=solver, backend=sage, steps=2

Status:  complete
Output:  Okay, let's find the inverse Laplace transform of s / (s² + 4) and verify our answer! First, we compute the inverse Laplace transform of s / (s² + 4), which yields cos(2t). Next, we take the Laplace transform of cos(2t), resulting in s / (s² + 4).  This confirms that our inverse transform was correct. Therefore, the inverse Laplace transform of s / (s² + 4) is cos(2t).
LLM calls: 2  Latency: 9925ms
Workers: mac-wens-Mac-mini.local, papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215337.md
```

