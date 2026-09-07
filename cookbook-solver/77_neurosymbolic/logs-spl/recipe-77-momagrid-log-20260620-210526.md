# Recipe-77 Momagrid experiment run 20260620-210526

DB source: `exp-momagrid-20260620-210526`
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
INFO:spl.adapters.momagrid:Task f16b2899-556c-472d-9007-9fa9758106e3 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f16b2899-556c-472d-9007-9fa9758106e3 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f16b2899-556c-472d-9007-9fa9758106e3 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f16b2899-556c-472d-9007-9fa9758106e3 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f16b2899-556c-472d-9007-9fa9758106e3 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f16b2899-556c-472d-9007-9fa9758106e3 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task f16b2899-556c-472d-9007-9fa9758106e3 completed by agent mac-wens-Mac-mini.local in 5747ms (21 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 21 tokens, 8071ms
INFO:spl.executor:GENERATE chain done -> @steps_text (39 chars total)
[INFO] [arm=solver] decomposed into 3 step(s):


3*x**3 - x|diff
PREV|factor
PREV|solve


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 40 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 137ms (0 LLM calls)
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
INFO:spl.adapters.momagrid:Task e178fde2-c95c-46f8-91d9-7477fffd1042 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/e178fde2-c95c-46f8-91d9-7477fffd1042 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/e178fde2-c95c-46f8-91d9-7477fffd1042 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/e178fde2-c95c-46f8-91d9-7477fffd1042 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/e178fde2-c95c-46f8-91d9-7477fffd1042 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/e178fde2-c95c-46f8-91d9-7477fffd1042 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task e178fde2-c95c-46f8-91d9-7477fffd1042 completed by agent papa-game in 5694ms (135 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 135 tokens, 8062ms
INFO:spl.executor:GENERATE chain done -> @result (493 chars total)
INFO:spl.executor:RETURN: 493 chars | status=complete, arm=solver, backend=sympy, steps=3

Status:  complete
Output:  Okay, let's break down this problem! We were asked to find the derivative of the expression 3*x**3 - x, then factor it if possible, and finally solve for the values of *x* that make the factored expression equal to zero. First, we differentiated the original expression to get 9*x**2 - 1.  Next, we factored the resulting quadratic expression: (3*x - 1)*(3*x + 1). Finally, setting this factored form equal to zero allows us to solve for *x*, which gives us the solutions x = -1/3 and x = 1/3.
LLM calls: 2  Latency: 16274ms
Workers: mac-wens-Mac-mini.local, papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma3-20260620-210527.md
```

