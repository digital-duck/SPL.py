# Recipe-77 Momagrid experiment run 20260620-212004

DB source: `exp-momagrid-20260620-212004`
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
[INFO] [arm=solver] Problem 'differentiate x**4 - 2*x**2 + 1' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 16d7da7f-bce4-45aa-bda7-13e67f23bafe submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/16d7da7f-bce4-45aa-bda7-13e67f23bafe "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/16d7da7f-bce4-45aa-bda7-13e67f23bafe "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/16d7da7f-bce4-45aa-bda7-13e67f23bafe "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 16d7da7f-bce4-45aa-bda7-13e67f23bafe completed by agent papa-game in 1418ms (22 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 22 tokens, 4043ms
INFO:spl.executor:GENERATE chain done -> @steps_text (33 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


x**4 - 2*x**2 + 1|diff
PREV|diff


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 51 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 162ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] d/dx(x**4 - 2*x**2 + 1) = 4*x**3 - 4*x
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 44 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 2ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] d/dx(4*x**3 - 4*x) = 12*x**2 - 4
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task f7980b31-b332-484e-a308-4cbcf8c278fe submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f7980b31-b332-484e-a308-4cbcf8c278fe "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f7980b31-b332-484e-a308-4cbcf8c278fe "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f7980b31-b332-484e-a308-4cbcf8c278fe "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f7980b31-b332-484e-a308-4cbcf8c278fe "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task f7980b31-b332-484e-a308-4cbcf8c278fe completed by agent papa-game in 3188ms (131 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 131 tokens, 6039ms
INFO:spl.executor:GENERATE chain done -> @result (396 chars total)
INFO:spl.executor:RETURN: 396 chars | status=complete, arm=solver, backend=sympy, steps=2

Status:  complete
Output:  Okay, let’s break down this problem! We need to find the derivative of the function f(x) = x⁴ - 2x² + 1.  First, we apply the power rule to each term: the derivative of x⁴ is 4x³, the derivative of -2x² is -4x, and the derivative of 1 is 0. This gives us 4x³ - 4x. Next, we take the derivative of this result which is 12x². Finally, subtracting off the term -4x yields our final answer: 12x² - 4.
LLM calls: 2  Latency: 10248ms
Workers: papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-212004.md
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
[INFO] [arm=solver] Problem 'expand (x+1)**2, then factor the expanded form' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 1f2b3dd5-2b9c-443b-821c-73d656d66be6 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1f2b3dd5-2b9c-443b-821c-73d656d66be6 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1f2b3dd5-2b9c-443b-821c-73d656d66be6 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1f2b3dd5-2b9c-443b-821c-73d656d66be6 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 1f2b3dd5-2b9c-443b-821c-73d656d66be6 completed by agent wengong in 1382ms (16 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 16 tokens, 4044ms
INFO:spl.executor:GENERATE chain done -> @steps_text (30 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


(x + 1)**2|expand
PREV|factor


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 50 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 160ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] expand((x + 1)**2) = x**2 + 2*x + 1
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 46 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] factor(x**2 + 2*x + 1) = (x + 1)**2
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 67d95382-cbed-4562-8e5c-d1a7b994f53a submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/67d95382-cbed-4562-8e5c-d1a7b994f53a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/67d95382-cbed-4562-8e5c-d1a7b994f53a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/67d95382-cbed-4562-8e5c-d1a7b994f53a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/67d95382-cbed-4562-8e5c-d1a7b994f53a "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 67d95382-cbed-4562-8e5c-d1a7b994f53a completed by agent mac-wens-Mac-mini.local in 3633ms (109 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 109 tokens, 6043ms
INFO:spl.executor:GENERATE chain done -> @result (376 chars total)
INFO:spl.executor:RETURN: 376 chars | status=complete, arm=solver, backend=sympy, steps=2

Status:  complete
Output:  Okay, let's expand (x + 1)² and then factor the resulting expression. First, we expand (x + 1)² which gives us x² + 2*x + 1. Next, we factor this quadratic expression, and it simplifies back to (x + 1)² because it’s a perfect square trinomial. Notice that it's just the original expression rearranged.  Therefore, the expanded and then factored form of (x+1)**2 is (x + 1)**2.
LLM calls: 2  Latency: 10248ms
Workers: mac-wens-Mac-mini.local, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-212004.md
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
[INFO] [arm=solver] Problem 'simplify the rational expression (x**2 - 1) / (x - 1)' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 25d60cfe-47ba-4cc7-9a59-e8916e5285e5 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/25d60cfe-47ba-4cc7-9a59-e8916e5285e5 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/25d60cfe-47ba-4cc7-9a59-e8916e5285e5 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/25d60cfe-47ba-4cc7-9a59-e8916e5285e5 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 25d60cfe-47ba-4cc7-9a59-e8916e5285e5 completed by agent mac-wens-Mac-mini.local in 1053ms (21 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 21 tokens, 4047ms
INFO:spl.executor:GENERATE chain done -> @steps_text (42 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


(x**2 - 1)/(x - 1)|simplify
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 42 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 189ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] simplify((x**2 - 1)/(x - 1)) = x + 1
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 29 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] simplify(x + 1) = x + 1
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task fe38b279-75d8-4d0c-b53f-a30f6fab578d submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/fe38b279-75d8-4d0c-b53f-a30f6fab578d "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/fe38b279-75d8-4d0c-b53f-a30f6fab578d "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/fe38b279-75d8-4d0c-b53f-a30f6fab578d "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/fe38b279-75d8-4d0c-b53f-a30f6fab578d "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task fe38b279-75d8-4d0c-b53f-a30f6fab578d completed by agent wengong in 3057ms (118 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 118 tokens, 6035ms
INFO:spl.executor:GENERATE chain done -> @result (352 chars total)
INFO:spl.executor:RETURN: 352 chars | status=complete, arm=solver, backend=sympy, steps=2

Status:  complete
Output:  Okay, let’s simplify the expression (x² - 1) / (x - 1). First, we recognize that x² - 1 is a difference of squares and can be factored into (x - 1)(x + 1).  This gives us (x - 1)(x + 1) / (x - 1). Now, we can cancel out one of the (x - 1) terms from the numerator and denominator. This leaves us with x + 1. Finally, the simplified expression is x + 1.
LLM calls: 2  Latency: 10273ms
Workers: mac-wens-Mac-mini.local, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-212004.md
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
[INFO] [arm=solver] Problem 'differentiate 3*x**3-x, then factor if needed, finally solve for x' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 6bade530-04b9-42cd-9e5a-537ea9a8c0d8 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/6bade530-04b9-42cd-9e5a-537ea9a8c0d8 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/6bade530-04b9-42cd-9e5a-537ea9a8c0d8 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 6bade530-04b9-42cd-9e5a-537ea9a8c0d8 completed by agent mac-wens-Mac-mini.local in 1021ms (21 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 21 tokens, 2037ms
INFO:spl.executor:GENERATE chain done -> @steps_text (39 chars total)
[INFO] [arm=solver] decomposed into 3 step(s):


3*x**3 - x|diff
PREV|factor
PREV|solve


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 40 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 161ms (0 LLM calls)
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
INFO:spl.adapters.momagrid:Task d870bd81-2e94-45c4-9843-a34b23a59169 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/d870bd81-2e94-45c4-9843-a34b23a59169 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/d870bd81-2e94-45c4-9843-a34b23a59169 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/d870bd81-2e94-45c4-9843-a34b23a59169 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task d870bd81-2e94-45c4-9843-a34b23a59169 completed by agent wengong in 3277ms (136 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 136 tokens, 4048ms
INFO:spl.executor:GENERATE chain done -> @result (500 chars total)
INFO:spl.executor:RETURN: 500 chars | status=complete, arm=solver, backend=sympy, steps=3

Status:  complete
Output:  Okay, let's break down this problem! We were asked to find the derivative of the expression 3*x**3 - x, then factor it if possible, and finally solve for the values of *x* that make the factored expression equal to zero. First, we differentiated the original expression, getting us the result:  9*x**2 - 1. Next, we factored this quadratic expression into (3*x - 1)*(3*x + 1). Finally, setting this factored form equal to zero allows us to solve for *x*, giving us the solutions x = -1/3 and x = 1/3.
LLM calls: 2  Latency: 6250ms
Workers: mac-wens-Mac-mini.local, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-212015.md
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
INFO:spl.adapters.momagrid:Task f2455ffc-3574-4d68-a198-bd439c2f79c4 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f2455ffc-3574-4d68-a198-bd439c2f79c4 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f2455ffc-3574-4d68-a198-bd439c2f79c4 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task f2455ffc-3574-4d68-a198-bd439c2f79c4 completed by agent papa-game in 1286ms (17 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 17 tokens, 2024ms
INFO:spl.executor:GENERATE chain done -> @steps_text (30 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


1/(x**2 - 1)|apart
PREV|apart


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 83 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 154ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] apart(1/(x**2 - 1)) = -1/(2*(x + 1)) + 1/(2*(x - 1))
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 101 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 3ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] apart(-1/(2*(x + 1)) + 1/(2*(x - 1))) = -1/(2*(x + 1)) + 1/(2*(x - 1))
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 86ab1d46-4461-4467-aa99-8ebc39ed9c22 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/86ab1d46-4461-4467-aa99-8ebc39ed9c22 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/86ab1d46-4461-4467-aa99-8ebc39ed9c22 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/86ab1d46-4461-4467-aa99-8ebc39ed9c22 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 86ab1d46-4461-4467-aa99-8ebc39ed9c22 completed by agent papa-game in 3398ms (144 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 144 tokens, 4044ms
INFO:spl.executor:GENERATE chain done -> @result (505 chars total)
INFO:spl.executor:RETURN: 505 chars | status=complete, arm=solver, backend=sympy, steps=2

Status:  complete
Output:  Okay, let's break down how to find the partial fraction decomposition of 1 / (x² - 1). We want to express this complex fraction as a sum of simpler fractions. The symbolic engine first divided the original expression by 2, resulting in:  -1/(2*(x + 1)) + 1/(2*(x - 1)). This step simply factored out a constant from each term.  The subsequent "apart" command confirmed this result as already being correct.  Therefore, the partial fraction decomposition of 1 / (x² - 1) is: -1/(2*(x + 1)) + 1/(2*(x - 1)).
LLM calls: 2  Latency: 6225ms
Workers: papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-212015.md
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
[INFO] [arm=solver] Problem 'expand (x-2)**3, then differentiate the result, then simplify it, then factor that, then solve for x = 0' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 91e88e57-8902-4c51-bd4e-2f348243a4ef submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/91e88e57-8902-4c51-bd4e-2f348243a4ef "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/91e88e57-8902-4c51-bd4e-2f348243a4ef "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 91e88e57-8902-4c51-bd4e-2f348243a4ef completed by agent wengong in 1337ms (31 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 31 tokens, 2037ms
INFO:spl.executor:GENERATE chain done -> @steps_text (65 chars total)
[INFO] [arm=solver] decomposed into 5 step(s):


(x - 2)**3|expand
PREV|diff
PREV|simplify
PREV|factor
PREV|solve


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 70 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 160ms (0 LLM calls)
[INFO] [arm=solver][step 1/5] expand((x - 2)**3) = x**3 - 6*x**2 + 12*x - 8
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 70 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 3ms (0 LLM calls)
[INFO] [arm=solver][step 2/5] d/dx(x**3 - 6*x**2 + 12*x - 8) = 3*x**2 - 12*x + 12
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 68 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 33ms (0 LLM calls)
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
INFO:spl.adapters.momagrid:Task ee8e7781-00ec-43c5-aa44-5fcd9265fcd1 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ee8e7781-00ec-43c5-aa44-5fcd9265fcd1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ee8e7781-00ec-43c5-aa44-5fcd9265fcd1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ee8e7781-00ec-43c5-aa44-5fcd9265fcd1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ee8e7781-00ec-43c5-aa44-5fcd9265fcd1 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task ee8e7781-00ec-43c5-aa44-5fcd9265fcd1 completed by agent mac-wens-Mac-mini.local in 4110ms (112 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 112 tokens, 6032ms
INFO:spl.executor:GENERATE chain done -> @result (321 chars total)
INFO:spl.executor:RETURN: 321 chars | status=complete, arm=solver, backend=sympy, steps=5

Status:  complete
Output:  Okay, let’s break down this problem! First, we expanded (x - 2)³ to get x³ - 6x² + 12x - 8.  Next, we differentiated that result and simplified it, arriving at the equation 3x² - 12x + 12.  Then, we factored this expression to obtain 3(x-2)² . Finally, solving for x in the equation 3(x-2)² = 0 yields the solution x = 2.
LLM calls: 2  Latency: 8270ms
Workers: mac-wens-Mac-mini.local, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-212015.md
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
[INFO] [arm=solver] Problem 'differentiate exp(x) and simplify it if necessary' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task f3437f58-87c3-4d46-881b-0918d75bcdf4 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f3437f58-87c3-4d46-881b-0918d75bcdf4 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f3437f58-87c3-4d46-881b-0918d75bcdf4 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f3437f58-87c3-4d46-881b-0918d75bcdf4 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task f3437f58-87c3-4d46-881b-0918d75bcdf4 completed by agent wengong in 1057ms (12 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 12 tokens, 4046ms
INFO:spl.executor:GENERATE chain done -> @steps_text (26 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


exp(x)|diff
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 28 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 139ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] d/dx(exp(x)) = exp(x)
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 32 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 45ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] simplify(exp(x)) = exp(x)
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 2b33f100-b137-46d7-8a22-5abf01d8c6f1 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2b33f100-b137-46d7-8a22-5abf01d8c6f1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2b33f100-b137-46d7-8a22-5abf01d8c6f1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2b33f100-b137-46d7-8a22-5abf01d8c6f1 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 2b33f100-b137-46d7-8a22-5abf01d8c6f1 completed by agent wengong in 2471ms (104 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 104 tokens, 4026ms
INFO:spl.executor:GENERATE chain done -> @result (433 chars total)
INFO:spl.executor:RETURN: 433 chars | status=complete, arm=solver, backend=sympy, steps=2

Status:  complete
Output:  Okay, let’s find the derivative of the function exp(x) and simplify it! The problem asks us to determine the instantaneous rate of change of the exponential function exp(x). First, we take the derivative of exp(x), which gives us exp(x). Then, we simplify this result – in this case, exp(x) remains unchanged. This step ensures our answer is in its simplest form. Therefore, the derivative of exp(x) and simplified, is simply exp(x).
LLM calls: 2  Latency: 8257ms
Workers: wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-212022.md
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
[INFO] [arm=solver] Problem 'find the limit of sin(x) divided by x as x approaches 0' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task d3a6ce73-f083-4bfc-a3bc-352ec51d0214 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/d3a6ce73-f083-4bfc-a3bc-352ec51d0214 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/d3a6ce73-f083-4bfc-a3bc-352ec51d0214 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/d3a6ce73-f083-4bfc-a3bc-352ec51d0214 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task d3a6ce73-f083-4bfc-a3bc-352ec51d0214 completed by agent mac-wens-Mac-mini.local in 968ms (19 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 19 tokens, 4046ms
INFO:spl.executor:GENERATE chain done -> @steps_text (34 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


sin(x)/x|limit(x,0)
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 27 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 149ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] limit(sin(x)/x, x->0) = 1
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 17 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] simplify(1) = 1
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 3f595c46-b9ba-47c4-969a-edba7cccde3e submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/3f595c46-b9ba-47c4-969a-edba7cccde3e "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/3f595c46-b9ba-47c4-969a-edba7cccde3e "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/3f595c46-b9ba-47c4-969a-edba7cccde3e "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/3f595c46-b9ba-47c4-969a-edba7cccde3e "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 3f595c46-b9ba-47c4-969a-edba7cccde3e completed by agent papa-game in 2708ms (114 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 114 tokens, 6037ms
INFO:spl.executor:GENERATE chain done -> @result (406 chars total)
INFO:spl.executor:RETURN: 406 chars | status=complete, arm=solver, backend=sympy, steps=2

Status:  complete
Output:  Okay, let’s find the limit of the expression sin(x) / x as x gets closer and closer to zero. The symbolic engine first recognized this as limit(sin(x)/x, x->0) = 1.  Then, it simplified this result, confirming that 1 = 1. This means that when we examine what happens to the ratio of sine to x as x approaches zero, the value remains constant at 1. Therefore, the limit of sin(x) / x as x approaches 0 is 1.
LLM calls: 2  Latency: 10233ms
Workers: mac-wens-Mac-mini.local, papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-212022.md
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
[INFO] [arm=solver] Problem 'expand sin(x) as a Taylor series around x = 0, keeping terms up to degree 5' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task c352e64e-9abd-47bb-bc77-4880d010a9fd submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/c352e64e-9abd-47bb-bc77-4880d010a9fd "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/c352e64e-9abd-47bb-bc77-4880d010a9fd "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/c352e64e-9abd-47bb-bc77-4880d010a9fd "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task c352e64e-9abd-47bb-bc77-4880d010a9fd completed by agent mac-wens-Mac-mini.local in 1341ms (32 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 32 tokens, 4038ms
INFO:spl.executor:GENERATE chain done -> @steps_text (82 chars total)
[INFO] [arm=solver] decomposed into 6 step(s):


sin(x)|series
PREV|expand
PREV|simplify
PREV|simplify
PREV|simplify
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 72 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 143ms (0 LLM calls)
[INFO] [arm=solver][step 1/6] series(sin(x), x=0, deg≤5) = x**5/120 - x**3/6 + x
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 75 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 2/6] expand(x**5/120 - x**3/6 + x) = x**5/120 - x**3/6 + x
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 77 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 36ms (0 LLM calls)
[INFO] [arm=solver][step 3/6] simplify(x**5/120 - x**3/6 + x) = x**5/120 - x**3/6 + x
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 77 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 3ms (0 LLM calls)
[INFO] [arm=solver][step 4/6] simplify(x**5/120 - x**3/6 + x) = x**5/120 - x**3/6 + x
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 77 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 3ms (0 LLM calls)
[INFO] [arm=solver][step 5/6] simplify(x**5/120 - x**3/6 + x) = x**5/120 - x**3/6 + x
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 77 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 3ms (0 LLM calls)
[INFO] [arm=solver][step 6/6] simplify(x**5/120 - x**3/6 + x) = x**5/120 - x**3/6 + x
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task ebe77157-a351-42f2-a8a0-6e0303e67598 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ebe77157-a351-42f2-a8a0-6e0303e67598 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ebe77157-a351-42f2-a8a0-6e0303e67598 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ebe77157-a351-42f2-a8a0-6e0303e67598 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ebe77157-a351-42f2-a8a0-6e0303e67598 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ebe77157-a351-42f2-a8a0-6e0303e67598 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task ebe77157-a351-42f2-a8a0-6e0303e67598 completed by agent mac-wens-Mac-mini.local in 5734ms (168 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 168 tokens, 8053ms
INFO:spl.executor:GENERATE chain done -> @result (659 chars total)
INFO:spl.executor:RETURN: 659 chars | status=complete, arm=solver, backend=sympy, steps=6

Status:  complete
Output:  Here’s an explanation of how we can expand sin(x) using its Taylor series around x = 0, including terms up to degree 5:

The student asked us to find the Taylor series representation for sin(x) centered at 0, including five terms.  First, the engine recognized this as a series expansion and initially calculated it as x⁵/120 - x³/6 + x. Then, it simplified this expression, which remained unchanged throughout the process: x⁵/120 - x³/6 + x.  This simplification repeated itself to ensure consistency in the final representation, confirming the exact result. Therefore, the Taylor series expansion of sin(x) around x = 0 up to degree 5 is: x⁵/120 - x³/6 + x.
LLM calls: 2  Latency: 12282ms
Workers: mac-wens-Mac-mini.local
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-212024.md
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
[INFO] [arm=solver] Problem 'simplify sin(x)**2 + cos(x)**2 using trigonometric identities' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 46365e40-d145-47af-9273-d16849e5e407 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/46365e40-d145-47af-9273-d16849e5e407 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/46365e40-d145-47af-9273-d16849e5e407 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/46365e40-d145-47af-9273-d16849e5e407 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 46365e40-d145-47af-9273-d16849e5e407 completed by agent papa-game in 1273ms (18 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 18 tokens, 4044ms
INFO:spl.executor:GENERATE chain done -> @steps_text (36 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


sin(x)**2 + cos(x)**2|simplify
PREV


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 37 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 204ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] simplify(sin(x)**2 + cos(x)**2) = 1
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 18 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] 1 (pass-through)
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 88b5048e-93fd-461a-888f-e8b43a95bb38 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/88b5048e-93fd-461a-888f-e8b43a95bb38 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/88b5048e-93fd-461a-888f-e8b43a95bb38 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/88b5048e-93fd-461a-888f-e8b43a95bb38 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 88b5048e-93fd-461a-888f-e8b43a95bb38 completed by agent wengong in 2192ms (82 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 82 tokens, 4036ms
INFO:spl.executor:GENERATE chain done -> @result (378 chars total)
INFO:spl.executor:RETURN: 378 chars | status=complete, arm=solver, backend=sympy, steps=2

Status:  complete
Output:  The student wanted to simplify the expression sin²(x) + cos²(x). The symbolic engine first recognized that this is a fundamental trigonometric identity, specifically stating that sin²(x) + cos²(x) = 1.  This result then passed through unchanged as "1". Essentially, the engine correctly identified and applied the Pythagorean identity. Therefore, the simplified expression is 1.
LLM calls: 2  Latency: 8286ms
Workers: papa-game, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-212031.md
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
[INFO] [arm=solver] Problem 'integrate the square root of (4 minus x squared)' — planning the chain (backend=sage) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 833607ef-a6d0-439c-8dd0-3356d17fb12f submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/833607ef-a6d0-439c-8dd0-3356d17fb12f "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/833607ef-a6d0-439c-8dd0-3356d17fb12f "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 833607ef-a6d0-439c-8dd0-3356d17fb12f completed by agent papa-game in 890ms (15 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 15 tokens, 2032ms
INFO:spl.executor:GENERATE chain done -> @steps_text (36 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


√(4 - x**2)|integrate
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 110 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1827ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] integral of √(4 - x**2) dx = 1/2*sqrt(-x^2 + 4)*x + 2*arcsin(1/2*x) + C
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 128 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 16ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] simplify(1/2*sqrt(-x^2 + 4)*x + 2*arcsin(1/2*x)) = 1/2*sqrt(-x^2 + 4)*x + 2*arcsin(1/2*x)
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task a3696fc3-1ef5-49d6-bdb7-6a3ca864ce72 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a3696fc3-1ef5-49d6-bdb7-6a3ca864ce72 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a3696fc3-1ef5-49d6-bdb7-6a3ca864ce72 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a3696fc3-1ef5-49d6-bdb7-6a3ca864ce72 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a3696fc3-1ef5-49d6-bdb7-6a3ca864ce72 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task a3696fc3-1ef5-49d6-bdb7-6a3ca864ce72 completed by agent mac-wens-Mac-mini.local in 4649ms (155 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 155 tokens, 6038ms
INFO:spl.executor:GENERATE chain done -> @result (355 chars total)
INFO:spl.executor:RETURN: 355 chars | status=complete, arm=solver, backend=sage, steps=2

Status:  complete
Output:  Okay, let's find the indefinite integral of √(4 - x²).  First, we use a substitution: u = 4 - x², so du = -2x dx, and thus dx = -1/2 du. This gives us ∫√(4 - x²) dx = ∫√u * (-1/2) du = -1/2 ∫√u du. Next, integrating √u yields (-1/2)( (2/3) * u^(3/2)) + C = -(1/3) * u^(3/2) + C. Finally, substituting back u = 4 - x², we have  -(1/3) * (4 - x²)^(3/2) + C.
LLM calls: 2  Latency: 9914ms
Workers: mac-wens-Mac-mini.local, papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-212033.md
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
[INFO] [arm=solver] Problem 'find the integral of sin(x) times cos(x), then simplify the result' — planning the chain (backend=sage) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task e185727f-56dc-4cea-a13b-6fd65d6b858b submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/e185727f-56dc-4cea-a13b-6fd65d6b858b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/e185727f-56dc-4cea-a13b-6fd65d6b858b "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task e185727f-56dc-4cea-a13b-6fd65d6b858b completed by agent papa-game in 909ms (16 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 16 tokens, 2028ms
INFO:spl.executor:GENERATE chain done -> @steps_text (38 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


sin(x)*cos(x)|integrate
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 62 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1846ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] integral of sin(x)*cos(x) dx = -1/2*cos(x)^2 + C
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 53 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 6ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] simplify(-1/2*cos(x)^2) = -1/2*cos(x)^2
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task aa1ca775-9c83-4a99-963e-5846505017b4 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/aa1ca775-9c83-4a99-963e-5846505017b4 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/aa1ca775-9c83-4a99-963e-5846505017b4 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/aa1ca775-9c83-4a99-963e-5846505017b4 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task aa1ca775-9c83-4a99-963e-5846505017b4 completed by agent wengong in 2498ms (117 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 117 tokens, 4034ms
INFO:spl.executor:GENERATE chain done -> @result (381 chars total)
INFO:spl.executor:RETURN: 381 chars | status=complete, arm=solver, backend=sage, steps=2

Status:  complete
Output:  Okay, let's find the integral of sin(x) * cos(x) and simplify it! We started by calculating the indefinite integral of sin(x) * cos(x), which resulted in -1/2 * cos²(x) + C.  Next, we simply expressed this result as -1/2 * cos²(x).  This simplification leaves us with a concise representation of the antiderivative. Therefore, the integral of sin(x) * cos(x) is -1/2 * cos²(x) + C.
LLM calls: 2  Latency: 7916ms
Workers: papa-game, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-212037.md
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
INFO:spl.adapters.momagrid:Task 554f6cd0-7096-412b-8190-fb396de5e605 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/554f6cd0-7096-412b-8190-fb396de5e605 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/554f6cd0-7096-412b-8190-fb396de5e605 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/554f6cd0-7096-412b-8190-fb396de5e605 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 554f6cd0-7096-412b-8190-fb396de5e605 completed by agent papa-game in 1043ms (24 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 24 tokens, 4037ms
INFO:spl.executor:GENERATE chain done -> @steps_text (49 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


x + y - 5|solve_system
PREV - y - 1|solve_system


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 81 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1763ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] solve_system(x + y - 5) = [
[x == -r1 + 5, y == r1]
]
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 53 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[ERROR] [arm=solver] SOLVER FAILURE at step 2/2: PREV - y - 1: name 'PREV' is not defined
INFO:spl.executor:RETURN: 180 chars | status=solver_error, arm=solver, backend=sage, steps=2

Status:  complete
Output:  [SOLVER FAILURE] Step 2/2 could not be computed: PREV - y - 1: name 'PREV' is not defined
Verified chain up to this point:
1. solve_system(x + y - 5) = [
[x == -r1 + 5, y == r1]
]

LLM calls: 1  Latency: 5802ms
Workers: papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-212040.md
```


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
INFO:spl.adapters.momagrid:Task c1bb25c8-62d7-46ac-a390-b06cedf81350 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/c1bb25c8-62d7-46ac-a390-b06cedf81350 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/c1bb25c8-62d7-46ac-a390-b06cedf81350 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task c1bb25c8-62d7-46ac-a390-b06cedf81350 completed by agent mac-wens-Mac-mini.local in 913ms (16 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 16 tokens, 2027ms
INFO:spl.executor:GENERATE chain done -> @steps_text (28 chars total)
[INFO] [arm=solver] decomposed into 1 step(s):


[[1, 2], [3, 4]]|eigenvalues


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 115 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1844ms (0 LLM calls)
[INFO] [arm=solver][step 1/1] eigenvalues([[1, 2], [3, 4]]) = [-1/2*sqrt(33) + 5/2, 1/2*sqrt(33) + 5/2]
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task a7c3024d-6fbe-4ba2-97e4-47ec5daa079a submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a7c3024d-6fbe-4ba2-97e4-47ec5daa079a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a7c3024d-6fbe-4ba2-97e4-47ec5daa079a "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a7c3024d-6fbe-4ba2-97e4-47ec5daa079a "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task a7c3024d-6fbe-4ba2-97e4-47ec5daa079a completed by agent papa-game in 3525ms (155 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 155 tokens, 4036ms
INFO:spl.executor:GENERATE chain done -> @result (484 chars total)
INFO:spl.executor:RETURN: 484 chars | status=complete, arm=solver, backend=sage, steps=1

Status:  complete
Output:  Okay, let’s break down this problem! We need to find the eigenvalues of a specific 2x2 matrix: [[1, 2], [3, 4]]. The first step was calculating the eigenvalues, which turned out to be [-1/2*sqrt(33) + 5/2] and [1/2*sqrt(33) + 5/2]. These are the specific values that represent the characteristic equation's roots. Essentially, these eigenvalues tell us about the scaling factors of the matrix’s eigenvectors.  Therefore, the final answer is: [-1/2*sqrt(33) + 5/2, 1/2*sqrt(33) + 5/2].
LLM calls: 2  Latency: 7908ms
Workers: mac-wens-Mac-mini.local, papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-212043.md
```


## gemma3 (ollama) — backend=sage — solver=true — run 1

_Tier: T4 | Problem ID: `p018` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma3 \
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
[INFO] [arm=solver] Problem 'solve the ordinary differential equation y'(x) = y(x) with initial condition y(0) = 1' — planning the chain (backend=sage) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 01ccb4aa-6846-44c3-8555-f4d9fdbd42a2 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/01ccb4aa-6846-44c3-8555-f4d9fdbd42a2 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/01ccb4aa-6846-44c3-8555-f4d9fdbd42a2 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/01ccb4aa-6846-44c3-8555-f4d9fdbd42a2 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 01ccb4aa-6846-44c3-8555-f4d9fdbd42a2 completed by agent wengong in 1180ms (18 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 18 tokens, 4040ms
INFO:spl.executor:GENERATE chain done -> @steps_text (37 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


y(x).diff(x)|ode_solve
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 53 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1650ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] dsolve(y(x).diff(x) = 0) -> Eq(y(x), C1)
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 51 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[ERROR] [arm=solver] SOLVER FAILURE at step 2/2: Eq(y(x), C1): name 'Eq' is not defined
INFO:spl.executor:RETURN: 165 chars | status=solver_error, arm=solver, backend=sage, steps=2

Status:  complete
Output:  [SOLVER FAILURE] Step 2/2 could not be computed: Eq(y(x), C1): name 'Eq' is not defined
Verified chain up to this point:
1. dsolve(y(x).diff(x) = 0) -> Eq(y(x), C1)

LLM calls: 1  Latency: 5692ms
Workers: wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-212046.md
```


## gemma3 (ollama) — backend=sage — solver=true — run 1

_Tier: T4 | Problem ID: `p019` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma3 \
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
[INFO] [arm=solver] Problem 'find the Laplace transform of exp(-2*t)' — planning the chain (backend=sage) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 93a09e67-b254-449c-a174-0e961e9c3a63 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/93a09e67-b254-449c-a174-0e961e9c3a63 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/93a09e67-b254-449c-a174-0e961e9c3a63 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 93a09e67-b254-449c-a174-0e961e9c3a63 completed by agent mac-wens-Mac-mini.local in 935ms (15 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 15 tokens, 2028ms
INFO:spl.executor:GENERATE chain done -> @steps_text (30 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


exp(-2*t)|laplace
PREV|laplace


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 50 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1626ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] laplace_transform(exp(-2*t)) = 1/(s + 2)
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 58 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] laplace_transform(1/(s + 2)) = 1/((s + 2)*s)
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 750a5081-de10-4a44-a22b-c43213e3e93c submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/750a5081-de10-4a44-a22b-c43213e3e93c "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/750a5081-de10-4a44-a22b-c43213e3e93c "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/750a5081-de10-4a44-a22b-c43213e3e93c "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/750a5081-de10-4a44-a22b-c43213e3e93c "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 750a5081-de10-4a44-a22b-c43213e3e93c completed by agent mac-wens-Mac-mini.local in 3892ms (112 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 112 tokens, 6040ms
INFO:spl.executor:GENERATE chain done -> @result (394 chars total)
INFO:spl.executor:RETURN: 394 chars | status=complete, arm=solver, backend=sage, steps=2

Status:  complete
Output:  Okay, let's find the Laplace transform of the function exp(-2t). The Laplace transform converts a time-domain function into a frequency-domain representation. We started with exp(-2t) and correctly identified its Laplace transform as 1/(s + 2).  Then, we simplified 1/(s+2) by multiplying it by s, resulting in 1/((s + 2)*s). Therefore, the final Laplace transform of exp(-2t) is 1/((s + 2)*s).
LLM calls: 2  Latency: 9695ms
Workers: mac-wens-Mac-mini.local
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-212045.md
```


## gemma3 (ollama) — backend=sage — solver=true — run 1

_Tier: T5 | Problem ID: `p010` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma3 \
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
[INFO] [arm=solver] Problem 'find the general solution to the second order ODE y''(x) - 3*y'(x) + 2*y(x) = 0' — planning the chain (backend=sage) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 13d38e74-2d9f-41fc-b682-067dab6c922c submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/13d38e74-2d9f-41fc-b682-067dab6c922c "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/13d38e74-2d9f-41fc-b682-067dab6c922c "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 13d38e74-2d9f-41fc-b682-067dab6c922c completed by agent mac-wens-Mac-mini.local in 1745ms (42 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 42 tokens, 2033ms
INFO:spl.executor:GENERATE chain done -> @steps_text (66 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


y(x).diff(x,2) - 3*y(x).diff(x) + 2*y(x)|ode_solve
PREV|ode_solve


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 123 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1457ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] dsolve(y(x).diff(x,2) - 3*y(x).diff(x) + 2*y(x) = 0) -> Eq(y(x), (C1 + C2*exp(x))*exp(x))
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 72 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[ERROR] [arm=solver] SOLVER FAILURE at step 2/2: Eq(y(x), (C1 + C2*exp(x))*exp(x)): name 'Eq' is not defined
INFO:spl.executor:RETURN: 235 chars | status=solver_error, arm=solver, backend=sage, steps=2

Status:  complete
Output:  [SOLVER FAILURE] Step 2/2 could not be computed: Eq(y(x), (C1 + C2*exp(x))*exp(x)): name 'Eq' is not defined
Verified chain up to this point:
1. dsolve(y(x).diff(x,2) - 3*y(x).diff(x) + 2*y(x) = 0) -> Eq(y(x), (C1 + C2*exp(x))*exp(x))

LLM calls: 1  Latency: 3491ms
Workers: mac-wens-Mac-mini.local
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-212055.md
```


## gemma3 (ollama) — backend=sage — solver=true — run 1

_Tier: T5 | Problem ID: `p020` | Host: `mac-wens-Mac-mini.local`_

```bash
(spl123) $ spl3 run cookbook/77_neurosymbolic/symbolic_math.spl --kernel --llm momagrid:gemma3 \
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
[INFO] [arm=solver] Problem 'find all roots of x**4 - 1 and express each root in simplified form' — planning the chain (backend=sage) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 9e865612-2a66-4021-9d3f-a32daf6f1e22 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/9e865612-2a66-4021-9d3f-a32daf6f1e22 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/9e865612-2a66-4021-9d3f-a32daf6f1e22 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 9e865612-2a66-4021-9d3f-a32daf6f1e22 completed by agent wengong in 1097ms (15 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 15 tokens, 2035ms
INFO:spl.executor:GENERATE chain done -> @steps_text (29 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


x**4 - 1|solve
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 56 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1909ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] solve(x**4 - 1 = 0) -> x = [I, -1, -I, 1]
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 56 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] simplify([I, -1, -I, 1]) = [I, -1, -I, 1]
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 81562126-1565-47e4-8d11-fd4e5a110123 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/81562126-1565-47e4-8d11-fd4e5a110123 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/81562126-1565-47e4-8d11-fd4e5a110123 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/81562126-1565-47e4-8d11-fd4e5a110123 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/81562126-1565-47e4-8d11-fd4e5a110123 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 81562126-1565-47e4-8d11-fd4e5a110123 completed by agent papa-game in 3422ms (146 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 146 tokens, 6046ms
INFO:spl.executor:GENERATE chain done -> @result (416 chars total)
INFO:spl.executor:RETURN: 416 chars | status=complete, arm=solver, backend=sage, steps=2

Status:  complete
Output:  Okay, let's break down this math problem! We’re looking to find all the roots of the equation x⁴ - 1 = 0.  First, we add 1 to both sides, resulting in x⁴ = 1. Next, we take the fourth root of both sides and solve for x, which gives us x = [I, -1, -I, 1]. This means our roots are i, -1, -i, and 1.  Essentially, the solutions to this equation are 1, -1, *i*, and *-i*. So, the final answer is: x = [1, -1, *i*, -*i*]
LLM calls: 2  Latency: 9992ms
Workers: papa-game, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-212053.md
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
INFO:spl.adapters.momagrid:Task 44d3de64-ccec-4c5c-8a90-d06e6f806e1c submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/44d3de64-ccec-4c5c-8a90-d06e6f806e1c "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/44d3de64-ccec-4c5c-8a90-d06e6f806e1c "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/44d3de64-ccec-4c5c-8a90-d06e6f806e1c "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 44d3de64-ccec-4c5c-8a90-d06e6f806e1c completed by agent papa-game in 1246ms (16 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 16 tokens, 4038ms
INFO:spl.executor:GENERATE chain done -> @steps_text (24 chars total)
[INFO] [arm=solver] decomposed into 1 step(s):


1/n**2|summation(n,1,oo)


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 47 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1849ms (0 LLM calls)
[INFO] [arm=solver][step 1/1] sum(1/n**2, n=1..+Infinity) = 1/6*pi^2
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task a89f5ddf-c5b1-4e1d-a655-c4717c57e640 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a89f5ddf-c5b1-4e1d-a655-c4717c57e640 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a89f5ddf-c5b1-4e1d-a655-c4717c57e640 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a89f5ddf-c5b1-4e1d-a655-c4717c57e640 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/a89f5ddf-c5b1-4e1d-a655-c4717c57e640 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task a89f5ddf-c5b1-4e1d-a655-c4717c57e640 completed by agent wengong in 3189ms (131 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 131 tokens, 6045ms
INFO:spl.executor:GENERATE chain done -> @result (482 chars total)
INFO:spl.executor:RETURN: 482 chars | status=complete, arm=solver, backend=sage, steps=1

Status:  complete
Output:  Okay, let's break down this calculation! The problem asks us to find the value of the infinite sum: 1/n² for all positive integers n, starting with n=1. The symbolic engine first simplified the entire sum as `sum(1/n**2, n=1..+Infinity)`.  Next, it evaluated this expression and reduced it to `1/6 * pi^2`. This intermediate result was then further processed into the final answer of `1/6 * pi^2`. Therefore, the symbolic sum of 1 over n squared from n equals 1 to infinity is π²/6.
LLM calls: 2  Latency: 11933ms
Workers: papa-game, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-212052.md
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
INFO:spl.adapters.momagrid:Task 9cfc97f9-c830-46f3-9252-0518b8539ff4 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/9cfc97f9-c830-46f3-9252-0518b8539ff4 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/9cfc97f9-c830-46f3-9252-0518b8539ff4 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/9cfc97f9-c830-46f3-9252-0518b8539ff4 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 9cfc97f9-c830-46f3-9252-0518b8539ff4 completed by agent mac-wens-Mac-mini.local in 1205ms (27 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 27 tokens, 4044ms
INFO:spl.executor:GENERATE chain done -> @steps_text (58 chars total)
[INFO] [arm=solver] decomposed into 3 step(s):


s / (s**2 + 4)|inverse_laplace
PREV|laplace
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 61 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1736ms (0 LLM calls)
[INFO] [arm=solver][step 1/3] inverse_laplace_transform(s / (s**2 + 4)) = cos(2*t)
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 53 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 2/3] laplace_transform(cos(2*t)) = s/(s^2 + 4)
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 47 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 7ms (0 LLM calls)
[INFO] [arm=solver][step 3/3] simplify(s/(s^2 + 4)) = s/(s^2 + 4)
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 26cbc01f-3794-46fb-9e64-143e0ba67ecc submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/26cbc01f-3794-46fb-9e64-143e0ba67ecc "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/26cbc01f-3794-46fb-9e64-143e0ba67ecc "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/26cbc01f-3794-46fb-9e64-143e0ba67ecc "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 26cbc01f-3794-46fb-9e64-143e0ba67ecc completed by agent papa-game in 2968ms (125 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 125 tokens, 4038ms
INFO:spl.executor:GENERATE chain done -> @result (452 chars total)
INFO:spl.executor:RETURN: 452 chars | status=complete, arm=solver, backend=sage, steps=3

Status:  complete
Output:  Okay, let's find the inverse Laplace transform of s / (s² + 4) and then verify our work. First, the symbolic engine determined that the inverse Laplace transform of s / (s² + 4) is cos(2t). Next, it calculated the Laplace transform of cos(2t), which correctly resulted in s / (s² + 4).  Then, it simplified this expression back to s / (s² + 4), confirming our initial transformation. Therefore, the inverse Laplace transform of s / (s² + 4) is cos(2t).
LLM calls: 2  Latency: 9828ms
Workers: mac-wens-Mac-mini.local, papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-212100.md
```

