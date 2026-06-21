# Recipe-77 Momagrid experiment run 20260620-205026

DB source: `exp-momagrid-20260620-205026`
Momagrid Hub: http://192.168.0.170:9000/
Workers: 3


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
[INFO] [arm=solver] Problem 'differentiate 3*x**3-x, then factor if needed, finally solve for x' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 2e1dd40a-e47b-4b13-9a76-697559e276ec submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2e1dd40a-e47b-4b13-9a76-697559e276ec "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2e1dd40a-e47b-4b13-9a76-697559e276ec "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2e1dd40a-e47b-4b13-9a76-697559e276ec "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2e1dd40a-e47b-4b13-9a76-697559e276ec "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 2e1dd40a-e47b-4b13-9a76-697559e276ec completed by agent papa-game in 4919ms (20 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 20 tokens, 6061ms
INFO:spl.executor:GENERATE chain done -> @steps_text (38 chars total)
[INFO] [arm=solver] decomposed into 3 step(s):


3*x**3 - x|diff
PREV|factor
PREV|solve


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 40 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 141ms (0 LLM calls)
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
INFO:spl.adapters.momagrid:Task e7edd93d-8c86-46fc-a979-a599f758cf43 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/e7edd93d-8c86-46fc-a979-a599f758cf43 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/e7edd93d-8c86-46fc-a979-a599f758cf43 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/e7edd93d-8c86-46fc-a979-a599f758cf43 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task e7edd93d-8c86-46fc-a979-a599f758cf43 completed by agent papa-game in 3413ms (132 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 132 tokens, 4041ms
INFO:spl.executor:GENERATE chain done -> @result (397 chars total)
INFO:spl.executor:RETURN: 397 chars | status=complete, arm=solver, backend=sympy, steps=3

Status:  complete
Output:  Okay, let’s break down this problem! We need to find the values of ‘x’ that make the expression `9*x**2 - 1` equal to zero and then factor it completely. First, we take the derivative of `3*x**3 - x`, which gives us `9*x**2 - 1`. Next, we factor this quadratic: `(3*x - 1)*(3*x + 1)`. Finally, setting each part equal to zero allows us to solve for ‘x’, giving us the solutions  `x = [-1/3, 1/3]`.
LLM calls: 2  Latency: 10247ms
Workers: papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-205026.md
```

