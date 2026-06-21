# Recipe-77 Momagrid experiment run 20260620-215022

DB source: `exp-momagrid-20260620-215022`
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
[INFO] [arm=solver] Problem 'differentiate 3*x**3-x, then factor if needed, finally solve for x' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 8be6ff05-ae41-46d7-839a-debcdafb3de7 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/8be6ff05-ae41-46d7-839a-debcdafb3de7 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/8be6ff05-ae41-46d7-839a-debcdafb3de7 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/8be6ff05-ae41-46d7-839a-debcdafb3de7 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 8be6ff05-ae41-46d7-839a-debcdafb3de7 completed by agent papa-game in 2653ms (20 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 20 tokens, 4045ms
INFO:spl.executor:GENERATE chain done -> @steps_text (38 chars total)
[INFO] [arm=solver] decomposed into 3 step(s):


3*x**3 - x|diff
PREV|factor
PREV|solve


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 40 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 142ms (0 LLM calls)
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
INFO:spl.adapters.momagrid:Task 6b9097e7-08ab-45ee-8356-dd1b462b8ece submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/6b9097e7-08ab-45ee-8356-dd1b462b8ece "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/6b9097e7-08ab-45ee-8356-dd1b462b8ece "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/6b9097e7-08ab-45ee-8356-dd1b462b8ece "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/6b9097e7-08ab-45ee-8356-dd1b462b8ece "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 6b9097e7-08ab-45ee-8356-dd1b462b8ece completed by agent papa-game in 3406ms (135 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 135 tokens, 6036ms
INFO:spl.executor:GENERATE chain done -> @result (486 chars total)
INFO:spl.executor:RETURN: 486 chars | status=complete, arm=solver, backend=sympy, steps=3

Status:  complete
Output:  Okay, let's break down this problem! We were asked to find the derivative of the expression 3*x**3 - x, then factor it if possible, and finally solve for the values of 'x' that make the factored expression equal to zero. First, we differentiated the original expression, finding the derivative to be 9*x**2 - 1. Next, we factored this result: (3*x - 1)*(3*x + 1).  Finally, setting this factored form equal to zero allows us to solve for x, giving us the solutions x = -1/3 and x = 1/3.
LLM calls: 2  Latency: 10227ms
Workers: papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215023.md
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
[INFO] [arm=solver] Problem 'expand (x+1)**2, then factor the expanded form' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 660c2ec9-a41f-4b3b-b62c-7b9c295be7bc submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/660c2ec9-a41f-4b3b-b62c-7b9c295be7bc "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/660c2ec9-a41f-4b3b-b62c-7b9c295be7bc "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/660c2ec9-a41f-4b3b-b62c-7b9c295be7bc "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/660c2ec9-a41f-4b3b-b62c-7b9c295be7bc "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 660c2ec9-a41f-4b3b-b62c-7b9c295be7bc completed by agent mac-wens-Mac-mini.local in 4554ms (16 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 16 tokens, 6050ms
INFO:spl.executor:GENERATE chain done -> @steps_text (30 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


(x + 1)**2|expand
PREV|factor


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 50 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 192ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] expand((x + 1)**2) = x**2 + 2*x + 1
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 46 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] factor(x**2 + 2*x + 1) = (x + 1)**2
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 4bca22af-f6f4-452a-bc05-768dea1341e1 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/4bca22af-f6f4-452a-bc05-768dea1341e1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/4bca22af-f6f4-452a-bc05-768dea1341e1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/4bca22af-f6f4-452a-bc05-768dea1341e1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/4bca22af-f6f4-452a-bc05-768dea1341e1 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 4bca22af-f6f4-452a-bc05-768dea1341e1 completed by agent mac-wens-Mac-mini.local in 3849ms (113 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 113 tokens, 6030ms
INFO:spl.executor:GENERATE chain done -> @result (328 chars total)
INFO:spl.executor:RETURN: 328 chars | status=complete, arm=solver, backend=sympy, steps=2

Status:  complete
Output:  Okay, let's expand (x + 1)² and then factor the resulting expression. First, we expand (x + 1)² which gives us x² + 2*x + 1. Next, we factor this quadratic expression: x² + 2*x + 1.  This factorization results in (x + 1) * (x + 1), or equivalently (x+1)**2. Therefore, the expanded and factored form of (x + 1)² is (x + 1)**2**.
LLM calls: 2  Latency: 12276ms
Workers: mac-wens-Mac-mini.local
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215023.md
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
[INFO] [arm=solver] Problem 'find the partial fraction decomposition of 1 / (x**2 - 1)' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 7669f15c-5b71-41a8-9c29-e79769fe1ef2 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/7669f15c-5b71-41a8-9c29-e79769fe1ef2 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/7669f15c-5b71-41a8-9c29-e79769fe1ef2 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/7669f15c-5b71-41a8-9c29-e79769fe1ef2 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/7669f15c-5b71-41a8-9c29-e79769fe1ef2 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 7669f15c-5b71-41a8-9c29-e79769fe1ef2 completed by agent wengong in 4520ms (17 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 17 tokens, 6052ms
INFO:spl.executor:GENERATE chain done -> @steps_text (30 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


1/(x**2 - 1)|apart
PREV|apart


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 83 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 195ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] apart(1/(x**2 - 1)) = -1/(2*(x + 1)) + 1/(2*(x - 1))
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 101 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 3ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] apart(-1/(2*(x + 1)) + 1/(2*(x - 1))) = -1/(2*(x + 1)) + 1/(2*(x - 1))
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 5c7ef0e7-c6c2-48a1-a914-548851a59a3a submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/5c7ef0e7-c6c2-48a1-a914-548851a59a3a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/5c7ef0e7-c6c2-48a1-a914-548851a59a3a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/5c7ef0e7-c6c2-48a1-a914-548851a59a3a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/5c7ef0e7-c6c2-48a1-a914-548851a59a3a "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 5c7ef0e7-c6c2-48a1-a914-548851a59a3a completed by agent wengong in 3717ms (162 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 162 tokens, 6028ms
INFO:spl.executor:GENERATE chain done -> @result (483 chars total)
INFO:spl.executor:RETURN: 483 chars | status=complete, arm=solver, backend=sympy, steps=2

Status:  complete
Output:  Okay, let's break down how to find the partial fraction decomposition of 1 / (x² - 1). The problem asks us to express this complex fraction as a sum of simpler fractions with linear terms.  First, the symbolic engine found that 1/(x² - 1) can be split into -1/(2(x + 1)) + 1/(2(x - 1)). Then, it simply repeated this step confirming the same result: -1/(2*(x + 1)) + 1/(2*(x - 1)).  Therefore, the partial fraction decomposition of 1 / (x² - 1) is **-1/(2*(x + 1)) + 1/(2*(x - 1))**.
LLM calls: 2  Latency: 12280ms
Workers: wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215023.md
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
[INFO] [arm=solver] Problem 'expand (x-2)**3, then differentiate the result, then simplify it, then factor that, then solve for x = 0' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task a197b3db-eec0-49ab-a94e-47cb8a429b5d submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a197b3db-eec0-49ab-a94e-47cb8a429b5d "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a197b3db-eec0-49ab-a94e-47cb8a429b5d "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a197b3db-eec0-49ab-a94e-47cb8a429b5d "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a197b3db-eec0-49ab-a94e-47cb8a429b5d "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task a197b3db-eec0-49ab-a94e-47cb8a429b5d completed by agent papa-game in 3562ms (31 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 31 tokens, 6043ms
INFO:spl.executor:GENERATE chain done -> @steps_text (65 chars total)
[INFO] [arm=solver] decomposed into 5 step(s):


(x - 2)**3|expand
PREV|diff
PREV|simplify
PREV|factor
PREV|solve


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 70 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 192ms (0 LLM calls)
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
INFO:spl.adapters.momagrid:Task 53b47116-8cfb-49c8-b84a-9414d3080de9 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/53b47116-8cfb-49c8-b84a-9414d3080de9 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/53b47116-8cfb-49c8-b84a-9414d3080de9 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/53b47116-8cfb-49c8-b84a-9414d3080de9 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/53b47116-8cfb-49c8-b84a-9414d3080de9 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 53b47116-8cfb-49c8-b84a-9414d3080de9 completed by agent papa-game in 4704ms (164 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 164 tokens, 6028ms
INFO:spl.executor:GENERATE chain done -> @result (506 chars total)
INFO:spl.executor:RETURN: 506 chars | status=complete, arm=solver, backend=sympy, steps=5

Status:  complete
Output:  Okay, let’s break down this problem! We were asked to expand (x - 2)**3, then differentiate the expanded form, simplify it, factorize it, and finally find the value of x when that factored expression equals zero.  First, we expanded (x - 2)**3 resulting in x**3 - 6*x**2 + 12*x - 8. Then, differentiating this gave us 3*x**2 - 12*x + 12. This result was then simplified to remain as 3*x**2 - 12*x + 12.  Factoring this expression yielded 3*(x - 2)**2 and solving for x when that equals zero, we find x = 2.
LLM calls: 2  Latency: 12308ms
Workers: papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215023.md
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
[INFO] [arm=solver] Problem 'simplify the rational expression (x**2 - 1) / (x - 1)' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 86b8d44f-2ac4-4ccd-a120-3898c61820cb submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/86b8d44f-2ac4-4ccd-a120-3898c61820cb "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/86b8d44f-2ac4-4ccd-a120-3898c61820cb "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/86b8d44f-2ac4-4ccd-a120-3898c61820cb "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/86b8d44f-2ac4-4ccd-a120-3898c61820cb "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 86b8d44f-2ac4-4ccd-a120-3898c61820cb completed by agent wengong in 4013ms (23 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 23 tokens, 6055ms
INFO:spl.executor:GENERATE chain done -> @steps_text (44 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


(x**2 - 1) / (x - 1)|simplify
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 44 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 228ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] simplify((x**2 - 1) / (x - 1)) = x + 1
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 29 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] simplify(x + 1) = x + 1
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task d8d40fce-00a1-4a6c-a80c-30cf185907bd submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/d8d40fce-00a1-4a6c-a80c-30cf185907bd "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/d8d40fce-00a1-4a6c-a80c-30cf185907bd "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/d8d40fce-00a1-4a6c-a80c-30cf185907bd "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/d8d40fce-00a1-4a6c-a80c-30cf185907bd "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/d8d40fce-00a1-4a6c-a80c-30cf185907bd "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task d8d40fce-00a1-4a6c-a80c-30cf185907bd completed by agent wengong in 5797ms (128 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 128 tokens, 8035ms
INFO:spl.executor:GENERATE chain done -> @result (372 chars total)
INFO:spl.executor:RETURN: 372 chars | status=complete, arm=solver, backend=sympy, steps=2

Status:  complete
Output:  Okay, let’s simplify the rational expression (x² - 1) / (x - 1). First, we recognize that x² - 1 is a difference of squares and can be factored: (x² - 1) = (x - 1)(x + 1).  So, the expression becomes ((x - 1)(x + 1)) / (x - 1). Now, we can cancel out one of the (x - 1) terms in the numerator and denominator, leaving us with x + 1. Finally, this simplified form is x + 1.
LLM calls: 2  Latency: 14321ms
Workers: wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215023.md
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
[INFO] [arm=solver] Problem 'differentiate x**4 - 2*x**2 + 1' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 1334757c-ceb0-4880-aac5-e31e92257b02 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1334757c-ceb0-4880-aac5-e31e92257b02 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1334757c-ceb0-4880-aac5-e31e92257b02 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1334757c-ceb0-4880-aac5-e31e92257b02 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1334757c-ceb0-4880-aac5-e31e92257b02 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1334757c-ceb0-4880-aac5-e31e92257b02 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 1334757c-ceb0-4880-aac5-e31e92257b02 completed by agent mac-wens-Mac-mini.local in 5647ms (32 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 32 tokens, 8061ms
INFO:spl.executor:GENERATE chain done -> @steps_text (57 chars total)
[INFO] [arm=solver] decomposed into 4 step(s):


x**4 - 2*x**2 + 1|diff
PREV|diff
PREV|diff
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 51 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 149ms (0 LLM calls)
[INFO] [arm=solver][step 1/4] d/dx(x**4 - 2*x**2 + 1) = 4*x**3 - 4*x
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 44 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 2ms (0 LLM calls)
[INFO] [arm=solver][step 2/4] d/dx(4*x**3 - 4*x) = 12*x**2 - 4
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 29 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 3/4] d/dx(12*x**2 - 4) = 24*x
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 26 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 31ms (0 LLM calls)
[INFO] [arm=solver][step 4/4] simplify(24*x) = 24*x
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 8f9df138-040a-42d1-8fd4-bfbeee2778cf submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/8f9df138-040a-42d1-8fd4-bfbeee2778cf "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/8f9df138-040a-42d1-8fd4-bfbeee2778cf "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/8f9df138-040a-42d1-8fd4-bfbeee2778cf "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/8f9df138-040a-42d1-8fd4-bfbeee2778cf "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/8f9df138-040a-42d1-8fd4-bfbeee2778cf "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 8f9df138-040a-42d1-8fd4-bfbeee2778cf completed by agent mac-wens-Mac-mini.local in 5416ms (111 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 111 tokens, 8043ms
INFO:spl.executor:GENERATE chain done -> @result (341 chars total)
INFO:spl.executor:RETURN: 341 chars | status=complete, arm=solver, backend=sympy, steps=4

Status:  complete
Output:  Okay, let’s find the derivative of the function x⁴ - 2x² + 1. We start by taking the derivative of each term individually: first, we get 4x³ - 4x. Then, we differentiate again to obtain 12x² - 4. Next, we take the derivative of that result, which yields 24x. Finally, this simplifies to 24x. Therefore, the derivative of x⁴ - 2x² + 1 is 24x.
LLM calls: 2  Latency: 16289ms
Workers: mac-wens-Mac-mini.local
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215023.md
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
INFO:spl.adapters.momagrid:Task d5435bd9-d931-4bcf-b35e-7cf1d4082f9a submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/d5435bd9-d931-4bcf-b35e-7cf1d4082f9a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/d5435bd9-d931-4bcf-b35e-7cf1d4082f9a "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task d5435bd9-d931-4bcf-b35e-7cf1d4082f9a completed by agent papa-game in 1756ms (44 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 44 tokens, 2026ms
INFO:spl.executor:GENERATE chain done -> @steps_text (94 chars total)
[INFO] [arm=solver] decomposed into 5 step(s):


√(4 - x**2)|integrate
PREV|simplify
PREV|trigsimp
PREV|acos(x/2)|acos
PREV|acos(x/2)|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 110 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1848ms (0 LLM calls)
[INFO] [arm=solver][step 1/5] integral of √(4 - x**2) dx = 1/2*sqrt(-x^2 + 4)*x + 2*arcsin(1/2*x) + C
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 128 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 12ms (0 LLM calls)
[INFO] [arm=solver][step 2/5] simplify(1/2*sqrt(-x^2 + 4)*x + 2*arcsin(1/2*x)) = 1/2*sqrt(-x^2 + 4)*x + 2*arcsin(1/2*x)
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 128 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 3/5] trigsimp(1/2*sqrt(-x^2 + 4)*x + 2*arcsin(1/2*x)) = 1/2*sqrt(-x^2 + 4)*x + 2*arcsin(1/2*x)
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 63 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[ERROR] [arm=solver] SOLVER FAILURE at step 4/5: unknown operation 'acos(x/2)' — not in Sage kernel
INFO:spl.executor:RETURN: 394 chars | status=solver_error, arm=solver, backend=sage, steps=4

Status:  complete
Output:  [SOLVER FAILURE] Step 4/5 could not be computed: unknown operation 'acos(x/2)' — not in Sage kernel
Verified chain up to this point:
1. integral of √(4 - x**2) dx = 1/2*sqrt(-x^2 + 4)*x + 2*arcsin(1/2*x) + C
2. simplify(1/2*sqrt(-x^2 + 4)*x + 2*arcsin(1/2*x)) = 1/2*sqrt(-x^2 + 4)*x + 2*arcsin(1/2*x)
3. trigsimp(1/2*sqrt(-x^2 + 4)*x + 2*arcsin(1/2*x)) = 1/2*sqrt(-x^2 + 4)*x + 2*arcsin(1/2*x)

LLM calls: 1  Latency: 3888ms
Workers: papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215037.md
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
INFO:spl.adapters.momagrid:Task 90abdbd3-d830-4a54-91b9-b74b196f54e8 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/90abdbd3-d830-4a54-91b9-b74b196f54e8 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/90abdbd3-d830-4a54-91b9-b74b196f54e8 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/90abdbd3-d830-4a54-91b9-b74b196f54e8 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 90abdbd3-d830-4a54-91b9-b74b196f54e8 completed by agent wengong in 2262ms (12 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 12 tokens, 4034ms
INFO:spl.executor:GENERATE chain done -> @steps_text (26 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


exp(x)|diff
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 28 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 98ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] d/dx(exp(x)) = exp(x)
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 32 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 45ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] simplify(exp(x)) = exp(x)
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 32c5b3d2-78ce-45a5-a348-afb4a74a6028 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/32c5b3d2-78ce-45a5-a348-afb4a74a6028 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/32c5b3d2-78ce-45a5-a348-afb4a74a6028 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/32c5b3d2-78ce-45a5-a348-afb4a74a6028 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/32c5b3d2-78ce-45a5-a348-afb4a74a6028 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 32c5b3d2-78ce-45a5-a348-afb4a74a6028 completed by agent mac-wens-Mac-mini.local in 3520ms (99 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 99 tokens, 6028ms
INFO:spl.executor:GENERATE chain done -> @result (415 chars total)
INFO:spl.executor:RETURN: 415 chars | status=complete, arm=solver, backend=sympy, steps=2

Status:  complete
Output:  Okay, let’s differentiate the function exp(x) and see if we can simplify it further. The student asked us to find the derivative of the exponential function exp(x).  Our symbolic math engine started by applying the basic differentiation rule: d/dx (exp(x)) = exp(x). Then, the engine simplified this result, confirming that exp(x) is already in its simplest form. Therefore, the derivative of exp(x) remains exp(x).
LLM calls: 2  Latency: 10206ms
Workers: mac-wens-Mac-mini.local, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215033.md
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
[INFO] [arm=solver] Problem 'find the limit of sin(x) divided by x as x approaches 0' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task de1da480-042a-4c40-abde-c0bb3b40e8ab submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/de1da480-042a-4c40-abde-c0bb3b40e8ab "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/de1da480-042a-4c40-abde-c0bb3b40e8ab "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/de1da480-042a-4c40-abde-c0bb3b40e8ab "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task de1da480-042a-4c40-abde-c0bb3b40e8ab completed by agent wengong in 1108ms (19 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 19 tokens, 4028ms
INFO:spl.executor:GENERATE chain done -> @steps_text (34 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


sin(x)/x|limit(x,0)
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 27 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 158ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] limit(sin(x)/x, x->0) = 1
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 17 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] simplify(1) = 1
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task c6b1bc40-1aaa-46fd-a244-5be0518a66df submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/c6b1bc40-1aaa-46fd-a244-5be0518a66df "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/c6b1bc40-1aaa-46fd-a244-5be0518a66df "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/c6b1bc40-1aaa-46fd-a244-5be0518a66df "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/c6b1bc40-1aaa-46fd-a244-5be0518a66df "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task c6b1bc40-1aaa-46fd-a244-5be0518a66df completed by agent papa-game in 3170ms (125 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 125 tokens, 6034ms
INFO:spl.executor:GENERATE chain done -> @result (535 chars total)
INFO:spl.executor:RETURN: 535 chars | status=complete, arm=solver, backend=sympy, steps=2

Status:  complete
Output:  Okay, let’s break down this problem! We're essentially asking: what value does sin(x) / x approach as x gets really close to zero? The engine first found that limit by evaluating the expression directly as x approaches 0 – it resulted in 1.  Then, it simplified that result, confirming that the limit is indeed equal to 1. This happens because the sine of a small angle is approximately equal to the angle itself when the angle is measured in radians. Therefore, sin(x)/x approaches 1 as x approaches zero. 

The final answer is **1**.
LLM calls: 2  Latency: 10221ms
Workers: papa-game, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215036.md
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
[INFO] [arm=solver] Problem 'expand sin(x) as a Taylor series around x = 0, keeping terms up to degree 5' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 105629fc-5330-4d24-9e17-700ff543b50e submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/105629fc-5330-4d24-9e17-700ff543b50e "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/105629fc-5330-4d24-9e17-700ff543b50e "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/105629fc-5330-4d24-9e17-700ff543b50e "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 105629fc-5330-4d24-9e17-700ff543b50e completed by agent mac-wens-Mac-mini.local in 1336ms (32 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 32 tokens, 4026ms
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
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 181ms (0 LLM calls)
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
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 47ms (0 LLM calls)
[INFO] [arm=solver][step 7/7] simplify(x**5/120 - x**3/6 + x) = x**5/120 - x**3/6 + x
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 5fcc5771-6de8-4a47-a4ab-dac14f395a56 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/5fcc5771-6de8-4a47-a4ab-dac14f395a56 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/5fcc5771-6de8-4a47-a4ab-dac14f395a56 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/5fcc5771-6de8-4a47-a4ab-dac14f395a56 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/5fcc5771-6de8-4a47-a4ab-dac14f395a56 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 5fcc5771-6de8-4a47-a4ab-dac14f395a56 completed by agent wengong in 3335ms (124 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 124 tokens, 6028ms
INFO:spl.executor:GENERATE chain done -> @result (411 chars total)
INFO:spl.executor:RETURN: 411 chars | status=complete, arm=solver, backend=sympy, steps=7

Status:  complete
Output:  The student asked us to find the Taylor series for sin(x) around x = 0, using up to five terms. First, we started with the expression `series(sin(x), x=0, deg≤5)`, which simplified to `x**5/120 - x**3/6 + x`.  This result was then passed through repeatedly as a pass-through step, appearing again in steps 2-6. Finally, the symbolic engine simplified this expression to its final form:  `x**5/120 - x**3/6 + x`.
LLM calls: 2  Latency: 10284ms
Workers: mac-wens-Mac-mini.local, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215036.md
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
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sage solver=true
[INFO] [arm=solver] Problem 'find the integral of sin(x) times cos(x), then simplify the result' — planning the chain (backend=sage) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task b0b29b73-ec95-4e6b-a2b8-6b28f8bf559b submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/b0b29b73-ec95-4e6b-a2b8-6b28f8bf559b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/b0b29b73-ec95-4e6b-a2b8-6b28f8bf559b "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task b0b29b73-ec95-4e6b-a2b8-6b28f8bf559b completed by agent wengong in 988ms (16 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 16 tokens, 2027ms
INFO:spl.executor:GENERATE chain done -> @steps_text (38 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


sin(x)*cos(x)|integrate
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 62 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1857ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] integral of sin(x)*cos(x) dx = -1/2*cos(x)^2 + C
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 53 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 6ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] simplify(-1/2*cos(x)^2) = -1/2*cos(x)^2
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task b43203b5-25be-487c-af7f-95bd98117487 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/b43203b5-25be-487c-af7f-95bd98117487 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/b43203b5-25be-487c-af7f-95bd98117487 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/b43203b5-25be-487c-af7f-95bd98117487 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task b43203b5-25be-487c-af7f-95bd98117487 completed by agent wengong in 3203ms (112 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 112 tokens, 4031ms
INFO:spl.executor:GENERATE chain done -> @result (339 chars total)
INFO:spl.executor:RETURN: 339 chars | status=complete, arm=solver, backend=sage, steps=2

Status:  complete
Output:  Okay, let's find the integral of sin(x) * cos(x) and simplify it! First, we use a u-substitution: letting u = cos(x), so du = -sin(x) dx. This transforms our integral to ∫ -du.  Next, we integrate -du with respect to u, which gives us -u + C. Finally, substituting back cos(x) for u, we get -cos(x) + C. So the final answer is -cos(x) + C.
LLM calls: 2  Latency: 7922ms
Workers: wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215039.md
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
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sympy solver=true
[INFO] [arm=solver] Problem 'simplify sin(x)**2 + cos(x)**2 using trigonometric identities' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task f1fb5fd1-1725-4882-b166-e6ccc6db3222 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f1fb5fd1-1725-4882-b166-e6ccc6db3222 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f1fb5fd1-1725-4882-b166-e6ccc6db3222 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f1fb5fd1-1725-4882-b166-e6ccc6db3222 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f1fb5fd1-1725-4882-b166-e6ccc6db3222 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task f1fb5fd1-1725-4882-b166-e6ccc6db3222 completed by agent papa-game in 2308ms (22 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 22 tokens, 6035ms
INFO:spl.executor:GENERATE chain done -> @steps_text (45 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


sin(x)**2 + cos(x)**2|trigsimp
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 37 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 193ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] trigsimp(sin(x)**2 + cos(x)**2) = 1
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 17 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] simplify(1) = 1
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task f1d595b1-0931-4f97-b311-7e3838a049c2 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f1d595b1-0931-4f97-b311-7e3838a049c2 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f1d595b1-0931-4f97-b311-7e3838a049c2 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f1d595b1-0931-4f97-b311-7e3838a049c2 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f1d595b1-0931-4f97-b311-7e3838a049c2 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task f1d595b1-0931-4f97-b311-7e3838a049c2 completed by agent mac-wens-Mac-mini.local in 2837ms (78 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 78 tokens, 6027ms
INFO:spl.executor:GENERATE chain done -> @result (288 chars total)
INFO:spl.executor:RETURN: 288 chars | status=complete, arm=solver, backend=sympy, steps=2

Status:  complete
Output:  The student wanted to simplify the expression sin(x)² + cos(x)². We started with `trigsimp(sin(x)**2 + cos(x)**2)`, which immediately simplified to 1.  Then, we applied `simplify(1)` to further refine the result. This step also yielded 1. Therefore, the simplified expression is simply 1.
LLM calls: 2  Latency: 12258ms
Workers: mac-wens-Mac-mini.local, papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215036.md
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
[INFO] [arm=solver] Problem 'solve the system of equations x + y = 5 and x - y = 1 for x and y' — planning the chain (backend=sage) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task f58137ac-bc1a-4d13-a1ad-8ab5f09e7c98 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f58137ac-bc1a-4d13-a1ad-8ab5f09e7c98 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f58137ac-bc1a-4d13-a1ad-8ab5f09e7c98 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f58137ac-bc1a-4d13-a1ad-8ab5f09e7c98 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f58137ac-bc1a-4d13-a1ad-8ab5f09e7c98 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task f58137ac-bc1a-4d13-a1ad-8ab5f09e7c98 completed by agent mac-wens-Mac-mini.local in 3661ms (24 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 24 tokens, 6036ms
INFO:spl.executor:GENERATE chain done -> @steps_text (49 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


x + y - 5|solve_system
PREV - y - 1|solve_system


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 81 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 2061ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] solve_system(x + y - 5) = [
[x == -r1 + 5, y == r1]
]
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 76 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[ERROR] [arm=solver] SOLVER FAILURE at step 2/2: ([
[x == -r1 + 5, y == r1]
]) - y - 1: name 'r1' is not defined
INFO:spl.executor:RETURN: 203 chars | status=solver_error, arm=solver, backend=sage, steps=2

Status:  complete
Output:  [SOLVER FAILURE] Step 2/2 could not be computed: ([
[x == -r1 + 5, y == r1]
]) - y - 1: name 'r1' is not defined
Verified chain up to this point:
1. solve_system(x + y - 5) = [
[x == -r1 + 5, y == r1]
]

LLM calls: 1  Latency: 8098ms
Workers: mac-wens-Mac-mini.local
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215042.md
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
[INFO] [arm=solver] Problem 'find the Laplace transform of exp(-2*t)' — planning the chain (backend=sage) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task e2572653-a92e-4eb7-91c2-8b2b62055178 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/e2572653-a92e-4eb7-91c2-8b2b62055178 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/e2572653-a92e-4eb7-91c2-8b2b62055178 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task e2572653-a92e-4eb7-91c2-8b2b62055178 completed by agent papa-game in 772ms (15 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 15 tokens, 2024ms
INFO:spl.executor:GENERATE chain done -> @steps_text (30 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


exp(-2*t)|laplace
PREV|laplace


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 50 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 2123ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] laplace_transform(exp(-2*t)) = 1/(s + 2)
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 58 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] laplace_transform(1/(s + 2)) = 1/((s + 2)*s)
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task ae68ea97-fea0-4cb1-a2eb-4d380ab1f97c submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ae68ea97-fea0-4cb1-a2eb-4d380ab1f97c "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ae68ea97-fea0-4cb1-a2eb-4d380ab1f97c "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ae68ea97-fea0-4cb1-a2eb-4d380ab1f97c "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task ae68ea97-fea0-4cb1-a2eb-4d380ab1f97c completed by agent papa-game in 2912ms (109 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 109 tokens, 4030ms
INFO:spl.executor:GENERATE chain done -> @result (391 chars total)
INFO:spl.executor:RETURN: 391 chars | status=complete, arm=solver, backend=sage, steps=2

Status:  complete
Output:  Okay, let’s break down this Laplace transform problem! We need to find the Laplace transform of the function exp(-2t). First, we take the Laplace transform of exp(-2t), which yields 1/(s + 2). Then, we transform 1/(s+2) into 1/((s+2)*s). This final result represents the complete Laplace transform of our original function. Therefore, the Laplace transform of exp(-2t) is indeed 1/((s+2)*s).
LLM calls: 2  Latency: 8179ms
Workers: papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215047.md
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
[INFO] [arm=solver] Problem 'find the eigenvalues of the 2 by 2 matrix with rows [1, 2] and [3, 4]' — planning the chain (backend=sage) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 480aa67b-c2bb-4934-818b-fb504f061811 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/480aa67b-c2bb-4934-818b-fb504f061811 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/480aa67b-c2bb-4934-818b-fb504f061811 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/480aa67b-c2bb-4934-818b-fb504f061811 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 480aa67b-c2bb-4934-818b-fb504f061811 completed by agent papa-game in 1253ms (16 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 16 tokens, 4038ms
INFO:spl.executor:GENERATE chain done -> @steps_text (28 chars total)
[INFO] [arm=solver] decomposed into 1 step(s):


[[1, 2], [3, 4]]|eigenvalues


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 115 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 2206ms (0 LLM calls)
[INFO] [arm=solver][step 1/1] eigenvalues([[1, 2], [3, 4]]) = [-1/2*sqrt(33) + 5/2, 1/2*sqrt(33) + 5/2]
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 89c8bcdd-f91b-4db6-9d77-bdb6922e2436 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/89c8bcdd-f91b-4db6-9d77-bdb6922e2436 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/89c8bcdd-f91b-4db6-9d77-bdb6922e2436 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/89c8bcdd-f91b-4db6-9d77-bdb6922e2436 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/89c8bcdd-f91b-4db6-9d77-bdb6922e2436 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 89c8bcdd-f91b-4db6-9d77-bdb6922e2436 completed by agent wengong in 3452ms (162 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 162 tokens, 6034ms
INFO:spl.executor:GENERATE chain done -> @result (440 chars total)
INFO:spl.executor:RETURN: 440 chars | status=complete, arm=solver, backend=sage, steps=1

Status:  complete
Output:  Okay, let's find the eigenvalues of the 2x2 matrix with rows [1, 2] and [3, 4]. The symbolic math engine first calculated the eigenvalues directly as:  [-1/2*sqrt(33) + 5/2, 1/2*sqrt(33) + 5/2]. This means the two eigenvalues are -√33 / 2 + 5/2 and √33 / 2 + 5/2. These specific values represent the characteristic equation's roots when solved for λ.  Therefore, the eigenvalues of the matrix are -1/2*sqrt(33) + 5/2 and 1/2*sqrt(33) + 5/2.
LLM calls: 2  Latency: 12280ms
Workers: papa-game, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215044.md
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
INFO:spl.adapters.momagrid:Task ae069d87-e9b4-46ea-be47-acbf805943f7 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ae069d87-e9b4-46ea-be47-acbf805943f7 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ae069d87-e9b4-46ea-be47-acbf805943f7 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ae069d87-e9b4-46ea-be47-acbf805943f7 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task ae069d87-e9b4-46ea-be47-acbf805943f7 completed by agent papa-game in 915ms (16 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 16 tokens, 4040ms
INFO:spl.executor:GENERATE chain done -> @steps_text (24 chars total)
[INFO] [arm=solver] decomposed into 1 step(s):


1/n**2|summation(n,1,oo)


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 47 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1956ms (0 LLM calls)
[INFO] [arm=solver][step 1/1] sum(1/n**2, n=1..+Infinity) = 1/6*pi^2
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 1bbf4f91-d35a-4c70-beba-a44f3f39d073 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1bbf4f91-d35a-4c70-beba-a44f3f39d073 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1bbf4f91-d35a-4c70-beba-a44f3f39d073 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1bbf4f91-d35a-4c70-beba-a44f3f39d073 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 1bbf4f91-d35a-4c70-beba-a44f3f39d073 completed by agent wengong in 2319ms (105 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 105 tokens, 4030ms
INFO:spl.executor:GENERATE chain done -> @result (423 chars total)
INFO:spl.executor:RETURN: 423 chars | status=complete, arm=solver, backend=sage, steps=1

Status:  complete
Output:  Okay, let’s break down this problem! The student was asking us to calculate the value of the infinite series where we sum up 1 divided by n squared, starting with n equals 1 and going on forever.  The engine first simplified the entire expression to just `1/6 * pi^2`. Then, it evaluated the summation, resulting in `1/6 * pi^2` as a final intermediate step. Finally, the engine arrived at the definitive answer:  **π²/6**.
LLM calls: 2  Latency: 10027ms
Workers: papa-game, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215048.md
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
INFO:spl.adapters.momagrid:Task a32f912f-b089-4d0f-9f02-939e9e698b69 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a32f912f-b089-4d0f-9f02-939e9e698b69 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a32f912f-b089-4d0f-9f02-939e9e698b69 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a32f912f-b089-4d0f-9f02-939e9e698b69 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task a32f912f-b089-4d0f-9f02-939e9e698b69 completed by agent mac-wens-Mac-mini.local in 1436ms (30 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 30 tokens, 4034ms
INFO:spl.executor:GENERATE chain done -> @steps_text (71 chars total)
[INFO] [arm=solver] decomposed into 5 step(s):


x**4 - 1|solve
PREV|simplify
PREV|simplify
PREV|simplify
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 56 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1853ms (0 LLM calls)
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
INFO:spl.adapters.momagrid:Task 26db1e2b-d067-44e0-9e10-05631c5afeb2 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/26db1e2b-d067-44e0-9e10-05631c5afeb2 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/26db1e2b-d067-44e0-9e10-05631c5afeb2 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/26db1e2b-d067-44e0-9e10-05631c5afeb2 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 26db1e2b-d067-44e0-9e10-05631c5afeb2 completed by agent papa-game in 2735ms (114 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 114 tokens, 4023ms
INFO:spl.executor:GENERATE chain done -> @result (394 chars total)
INFO:spl.executor:RETURN: 394 chars | status=complete, arm=solver, backend=sage, steps=5

Status:  complete
Output:  The question asked us to find all the solutions (roots) of the equation x⁴ - 1 = 0. The symbolic math engine first solved this equation, producing the roots: x = [I, -1, -I, 1].  It then simplified this list of roots, which remained unchanged at [I, -1, -I, 1].  The simplification process was repeated several times to confirm the root set. Therefore, the roots of x⁴ - 1 are i, -1, -i, and 1.
LLM calls: 2  Latency: 9912ms
Workers: mac-wens-Mac-mini.local, papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215048.md
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
INFO:spl.adapters.momagrid:Task 08fc02ae-e0c6-40f8-9f56-0f322af26037 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/08fc02ae-e0c6-40f8-9f56-0f322af26037 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/08fc02ae-e0c6-40f8-9f56-0f322af26037 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/08fc02ae-e0c6-40f8-9f56-0f322af26037 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 08fc02ae-e0c6-40f8-9f56-0f322af26037 completed by agent wengong in 1248ms (25 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 25 tokens, 4042ms
INFO:spl.executor:GENERATE chain done -> @steps_text (45 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


y(x).diff(x) - y(x)|ode_solve
PREV|ode_solve


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 64 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1509ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] dsolve(y(x).diff(x) - y(x) = 0) -> Eq(y(x), C1*exp(x))
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 51 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] C1*exp(x) (already solved — pass-through)
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 2c1e22f5-1e3e-4f59-a35e-fdc714b55515 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2c1e22f5-1e3e-4f59-a35e-fdc714b55515 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2c1e22f5-1e3e-4f59-a35e-fdc714b55515 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2c1e22f5-1e3e-4f59-a35e-fdc714b55515 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2c1e22f5-1e3e-4f59-a35e-fdc714b55515 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2c1e22f5-1e3e-4f59-a35e-fdc714b55515 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 2c1e22f5-1e3e-4f59-a35e-fdc714b55515 completed by agent mac-wens-Mac-mini.local in 4770ms (141 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 141 tokens, 8043ms
INFO:spl.executor:GENERATE chain done -> @result (483 chars total)
INFO:spl.executor:RETURN: 483 chars | status=complete, arm=solver, backend=sage, steps=2

Status:  complete
Output:  Okay, let's solve this differential equation! The problem asks us to find a function *y(x)* whose derivative is equal to itself, with the starting point y(0) = 1.  The symbolic engine first solves the equation y'(x) = y(x) and arrives at the general solution: y(x) = C1*exp(x), where C1 is an arbitrary constant. The step "C1*exp(x)" passes through as a result of that solution.  Finally, we apply the initial condition y(0) = 1 to find the value of C1, which gives us y(x) = exp(x).
LLM calls: 2  Latency: 13596ms
Workers: mac-wens-Mac-mini.local, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215047.md
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
INFO:spl.adapters.momagrid:Task 481c35b9-e1bc-4c79-9dd2-bff6ef015d75 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/481c35b9-e1bc-4c79-9dd2-bff6ef015d75 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/481c35b9-e1bc-4c79-9dd2-bff6ef015d75 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/481c35b9-e1bc-4c79-9dd2-bff6ef015d75 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 481c35b9-e1bc-4c79-9dd2-bff6ef015d75 completed by agent mac-wens-Mac-mini.local in 1784ms (42 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 42 tokens, 4044ms
INFO:spl.executor:GENERATE chain done -> @steps_text (66 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


y(x).diff(x,2) - 3*y(x).diff(x) + 2*y(x)|ode_solve
PREV|ode_solve


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 113 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1668ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] dsolve(y(x).diff(x,2) - 3*y(x).diff(x) + 2*y(x) = 0) -> Eq(y(x), (C1 + C2*exp(x))*exp(x))
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 79 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] (C1 + C2*exp(x))*exp(x) (already solved — pass-through)
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 1ffcc2ca-5de3-4a85-ae81-f9330d4518b4 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1ffcc2ca-5de3-4a85-ae81-f9330d4518b4 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1ffcc2ca-5de3-4a85-ae81-f9330d4518b4 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1ffcc2ca-5de3-4a85-ae81-f9330d4518b4 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 1ffcc2ca-5de3-4a85-ae81-f9330d4518b4 completed by agent wengong in 2788ms (136 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 136 tokens, 4027ms
INFO:spl.executor:GENERATE chain done -> @result (524 chars total)
INFO:spl.executor:RETURN: 524 chars | status=complete, arm=solver, backend=sage, steps=2

Status:  complete
Output:  Okay, let's solve this second-order ordinary differential equation: y''(x) - 3*y'(x) + 2*y(x) = 0. The symbolic math engine first recognized the equation and found a general solution expressed in terms of two arbitrary constants, C1 and C2, and the exponential function exp(x).  It then represented this solution as (C1 + C2*exp(x))*exp(x). This step essentially combined the constant term with the exponential part of the solution. The final solution to the given differential equation is therefore (C1 + C2*exp(x))*exp(x).
LLM calls: 2  Latency: 9740ms
Workers: mac-wens-Mac-mini.local, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215051.md
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
INFO:spl.adapters.momagrid:Task a09122e9-a706-48ce-94e9-972988ad95ef submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a09122e9-a706-48ce-94e9-972988ad95ef "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a09122e9-a706-48ce-94e9-972988ad95ef "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a09122e9-a706-48ce-94e9-972988ad95ef "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task a09122e9-a706-48ce-94e9-972988ad95ef completed by agent mac-wens-Mac-mini.local in 3541ms (22 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 22 tokens, 4046ms
INFO:spl.executor:GENERATE chain done -> @steps_text (44 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


s / (s**2 + 4)|inverse_laplace
PREV|laplace


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 61 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1783ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] inverse_laplace_transform(s / (s**2 + 4)) = cos(2*t)
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 53 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] laplace_transform(cos(2*t)) = s/(s^2 + 4)
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task b7ef3607-b250-45fe-b4a5-81438ac8a4d7 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/b7ef3607-b250-45fe-b4a5-81438ac8a4d7 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/b7ef3607-b250-45fe-b4a5-81438ac8a4d7 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/b7ef3607-b250-45fe-b4a5-81438ac8a4d7 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task b7ef3607-b250-45fe-b4a5-81438ac8a4d7 completed by agent wengong in 2688ms (110 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 110 tokens, 4033ms
INFO:spl.executor:GENERATE chain done -> @result (383 chars total)
INFO:spl.executor:RETURN: 383 chars | status=complete, arm=solver, backend=sage, steps=2

Status:  complete
Output:  Okay, let's find the inverse Laplace transform of s / (s² + 4) and then verify our result! First, we found that the inverse Laplace transform of s / (s² + 4) is cos(2t).  Next, we took the Laplace transform of cos(2t), which gave us s/(s² + 4). This confirms that our initial inverse Laplace transform was correct. Therefore, the inverse Laplace transform of s / (s² + 4) is cos(2t).
LLM calls: 2  Latency: 9866ms
Workers: mac-wens-Mac-mini.local, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-215055.md
```

