# Recipe-77 Momagrid experiment run 20260620-220333

DB source: `exp-momagrid-20260620-220333`
Momagrid Hub: http://192.168.0.170:9000/
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
[INFO] [arm=solver] Problem 'simplify the rational expression (x**2 - 1) / (x - 1)' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 1b7c95be-ff27-41fa-9763-82bd606c9008 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1b7c95be-ff27-41fa-9763-82bd606c9008 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1b7c95be-ff27-41fa-9763-82bd606c9008 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1b7c95be-ff27-41fa-9763-82bd606c9008 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1b7c95be-ff27-41fa-9763-82bd606c9008 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1b7c95be-ff27-41fa-9763-82bd606c9008 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1b7c95be-ff27-41fa-9763-82bd606c9008 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1b7c95be-ff27-41fa-9763-82bd606c9008 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1b7c95be-ff27-41fa-9763-82bd606c9008 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1b7c95be-ff27-41fa-9763-82bd606c9008 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1b7c95be-ff27-41fa-9763-82bd606c9008 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1b7c95be-ff27-41fa-9763-82bd606c9008 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/1b7c95be-ff27-41fa-9763-82bd606c9008 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 1b7c95be-ff27-41fa-9763-82bd606c9008 completed by agent mac-wens-Mac-mini.local in 18398ms (573 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 573 tokens, 22136ms
INFO:spl.executor:GENERATE chain done -> @steps_text (29 chars total)
[INFO] [arm=solver] decomposed into 1 step(s):


(x**2 - 1) / (x - 1)|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 44 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 182ms (0 LLM calls)
[INFO] [arm=solver][step 1/1] simplify((x**2 - 1) / (x - 1)) = x + 1
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task ea7ae891-0c98-46f2-8297-9f2e5642b15f submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ea7ae891-0c98-46f2-8297-9f2e5642b15f "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ea7ae891-0c98-46f2-8297-9f2e5642b15f "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ea7ae891-0c98-46f2-8297-9f2e5642b15f "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ea7ae891-0c98-46f2-8297-9f2e5642b15f "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ea7ae891-0c98-46f2-8297-9f2e5642b15f "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task ea7ae891-0c98-46f2-8297-9f2e5642b15f completed by agent papa-game in 6319ms (411 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 411 tokens, 8033ms
INFO:spl.executor:GENERATE chain done -> @result (252 chars total)
INFO:spl.executor:RETURN: 252 chars | status=complete, arm=solver, backend=sympy, steps=1

Status:  complete
Output:  The problem asks us to simplify the rational expression $\frac{x^2 - 1}{x - 1}$. To do this, we can factor the numerator. First, simplifying $(x^2 - 1)$ over $(x - 1)$ gives us $x + 1$. Therefore, the final simplified form of the expression is $x + 1$.
LLM calls: 2  Latency: 30353ms
Workers: mac-wens-Mac-mini.local, papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma4-e2b-20260620-220334.md
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
[INFO] [arm=solver] Problem 'find the partial fraction decomposition of 1 / (x**2 - 1)' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 149db7e4-c63a-41de-a74d-d71c10227d5f submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/149db7e4-c63a-41de-a74d-d71c10227d5f "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/149db7e4-c63a-41de-a74d-d71c10227d5f "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/149db7e4-c63a-41de-a74d-d71c10227d5f "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/149db7e4-c63a-41de-a74d-d71c10227d5f "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/149db7e4-c63a-41de-a74d-d71c10227d5f "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/149db7e4-c63a-41de-a74d-d71c10227d5f "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 149db7e4-c63a-41de-a74d-d71c10227d5f completed by agent mac-wens-Mac-mini.local in 7782ms (11 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 11 tokens, 10078ms
INFO:spl.executor:GENERATE chain done -> @steps_text (18 chars total)
[INFO] [arm=solver] decomposed into 1 step(s):


1/(x**2 - 1)|apart


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 83 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 230ms (0 LLM calls)
[INFO] [arm=solver][step 1/1] apart(1/(x**2 - 1)) = -1/(2*(x + 1)) + 1/(2*(x - 1))
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task bb708783-0c5a-45b5-9bf4-fd89a4d74c45 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/bb708783-0c5a-45b5-9bf4-fd89a4d74c45 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/bb708783-0c5a-45b5-9bf4-fd89a4d74c45 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/bb708783-0c5a-45b5-9bf4-fd89a4d74c45 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/bb708783-0c5a-45b5-9bf4-fd89a4d74c45 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/bb708783-0c5a-45b5-9bf4-fd89a4d74c45 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/bb708783-0c5a-45b5-9bf4-fd89a4d74c45 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/bb708783-0c5a-45b5-9bf4-fd89a4d74c45 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/bb708783-0c5a-45b5-9bf4-fd89a4d74c45 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/bb708783-0c5a-45b5-9bf4-fd89a4d74c45 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/bb708783-0c5a-45b5-9bf4-fd89a4d74c45 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/bb708783-0c5a-45b5-9bf4-fd89a4d74c45 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task bb708783-0c5a-45b5-9bf4-fd89a4d74c45 completed by agent mac-wens-Mac-mini.local in 16922ms (457 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 457 tokens, 20097ms
INFO:spl.executor:GENERATE chain done -> @result (500 chars total)
INFO:spl.executor:RETURN: 500 chars | status=complete, arm=solver, backend=sympy, steps=1

Status:  complete
Output:  The problem asks us to find the partial fraction decomposition for the expression $1 / (x^2 - 1)$. We use the symbolic math engine to break this rational function into simpler terms.
Following the exact steps computed by the engine:
1. Applying the partial fraction rule gives us: $-1/(2(x + 1)) + 1/(2(x - 1))$.
This is the complete partial fraction decomposition of the original expression.
Therefore, the partial fraction decomposition of $1 / (x^2 - 1)$ is $-\frac{1}{2(x+1)} + \frac{1}{2(x-1)}$.
LLM calls: 2  Latency: 30407ms
Workers: mac-wens-Mac-mini.local
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma4-e2b-20260620-220334.md
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
INFO:spl.adapters.momagrid:Task f73d3a96-d323-4358-ba2d-7b0d15e150ce submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f73d3a96-d323-4358-ba2d-7b0d15e150ce "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f73d3a96-d323-4358-ba2d-7b0d15e150ce "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f73d3a96-d323-4358-ba2d-7b0d15e150ce "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f73d3a96-d323-4358-ba2d-7b0d15e150ce "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f73d3a96-d323-4358-ba2d-7b0d15e150ce "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f73d3a96-d323-4358-ba2d-7b0d15e150ce "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f73d3a96-d323-4358-ba2d-7b0d15e150ce "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f73d3a96-d323-4358-ba2d-7b0d15e150ce "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f73d3a96-d323-4358-ba2d-7b0d15e150ce "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f73d3a96-d323-4358-ba2d-7b0d15e150ce "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f73d3a96-d323-4358-ba2d-7b0d15e150ce "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f73d3a96-d323-4358-ba2d-7b0d15e150ce "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f73d3a96-d323-4358-ba2d-7b0d15e150ce "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task f73d3a96-d323-4358-ba2d-7b0d15e150ce completed by agent papa-game in 21657ms (16 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 16 tokens, 24160ms
INFO:spl.executor:GENERATE chain done -> @steps_text (22 chars total)
[INFO] [arm=solver] decomposed into 1 step(s):


x**4 - 2*x**2 + 1|diff


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 51 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 165ms (0 LLM calls)
[INFO] [arm=solver][step 1/1] d/dx(x**4 - 2*x**2 + 1) = 4*x**3 - 4*x
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 4e41f756-2ad1-46ba-8eb3-706b6d8bde58 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/4e41f756-2ad1-46ba-8eb3-706b6d8bde58 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/4e41f756-2ad1-46ba-8eb3-706b6d8bde58 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/4e41f756-2ad1-46ba-8eb3-706b6d8bde58 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/4e41f756-2ad1-46ba-8eb3-706b6d8bde58 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/4e41f756-2ad1-46ba-8eb3-706b6d8bde58 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/4e41f756-2ad1-46ba-8eb3-706b6d8bde58 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/4e41f756-2ad1-46ba-8eb3-706b6d8bde58 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 4e41f756-2ad1-46ba-8eb3-706b6d8bde58 completed by agent mac-wens-Mac-mini.local in 10374ms (402 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 402 tokens, 12050ms
INFO:spl.executor:GENERATE chain done -> @result (346 chars total)
INFO:spl.executor:RETURN: 346 chars | status=complete, arm=solver, backend=sympy, steps=1

Status:  complete
Output:  To differentiate the expression $x^4 - 2x^2 + 1$, we use the power rule on each term individually. First, we take the derivative of $x^4$, which results in $4x^3$. Next, we find the derivative of $-2x^2$, which gives us $-4x$. Finally, the derivative of the constant $1$ is $0$. Combining these exact results yields the final answer: $4x^3 - 4x$.
LLM calls: 2  Latency: 36377ms
Workers: mac-wens-Mac-mini.local, papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma4-e2b-20260620-220334.md
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
INFO:spl.adapters.momagrid:Task be20921c-645a-43c1-94cd-639d64fb6c00 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/be20921c-645a-43c1-94cd-639d64fb6c00 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/be20921c-645a-43c1-94cd-639d64fb6c00 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/be20921c-645a-43c1-94cd-639d64fb6c00 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/be20921c-645a-43c1-94cd-639d64fb6c00 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/be20921c-645a-43c1-94cd-639d64fb6c00 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/be20921c-645a-43c1-94cd-639d64fb6c00 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/be20921c-645a-43c1-94cd-639d64fb6c00 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/be20921c-645a-43c1-94cd-639d64fb6c00 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/be20921c-645a-43c1-94cd-639d64fb6c00 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/be20921c-645a-43c1-94cd-639d64fb6c00 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/be20921c-645a-43c1-94cd-639d64fb6c00 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/be20921c-645a-43c1-94cd-639d64fb6c00 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/be20921c-645a-43c1-94cd-639d64fb6c00 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task be20921c-645a-43c1-94cd-639d64fb6c00 completed by agent papa-game in 21345ms (857 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 857 tokens, 24149ms
INFO:spl.executor:GENERATE chain done -> @steps_text (69 chars total)
[INFO] [arm=solver] decomposed into 5 step(s):


(x - 2)**3|expand
PREV|diff
PREV|simplify
PREV|factor
PREV|limit(x,0)


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 70 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 162ms (0 LLM calls)
[INFO] [arm=solver][step 1/5] expand((x - 2)**3) = x**3 - 6*x**2 + 12*x - 8
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 70 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 3ms (0 LLM calls)
[INFO] [arm=solver][step 2/5] d/dx(x**3 - 6*x**2 + 12*x - 8) = 3*x**2 - 12*x + 12
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 68 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 34ms (0 LLM calls)
[INFO] [arm=solver][step 3/5] simplify(3*x**2 - 12*x + 12) = 3*x**2 - 12*x + 12
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 54 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 4/5] factor(3*x**2 - 12*x + 12) = 3*(x - 2)**2
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 33 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 5/5] limit(3*(x - 2)**2, x->0) = 12
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 7f9c3a6a-4726-4eae-b71f-ecf301331871 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/7f9c3a6a-4726-4eae-b71f-ecf301331871 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/7f9c3a6a-4726-4eae-b71f-ecf301331871 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/7f9c3a6a-4726-4eae-b71f-ecf301331871 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/7f9c3a6a-4726-4eae-b71f-ecf301331871 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/7f9c3a6a-4726-4eae-b71f-ecf301331871 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/7f9c3a6a-4726-4eae-b71f-ecf301331871 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/7f9c3a6a-4726-4eae-b71f-ecf301331871 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/7f9c3a6a-4726-4eae-b71f-ecf301331871 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 7f9c3a6a-4726-4eae-b71f-ecf301331871 completed by agent papa-game in 10999ms (460 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 460 tokens, 14057ms
INFO:spl.executor:GENERATE chain done -> @result (395 chars total)
INFO:spl.executor:RETURN: 395 chars | status=complete, arm=solver, backend=sympy, steps=5

Status:  complete
Output:  The problem asks us to expand $(x-2)^3$, differentiate it, simplify the result, factor it, and finally find the limit as $x$ approaches 0.
First, expanding gives $x^3 - 6x^2 + 12x - 8$. Differentiating this yields $3x^2 - 12x + 12$. Simplifying does not change this result. Factoring leads to $3(x-2)^2$. Finally, taking the limit as $x$ approaches 0 gives the answer 12.
The final answer is 12.
LLM calls: 2  Latency: 38411ms
Workers: papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma4-e2b-20260620-220334.md
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
[INFO] [arm=solver] Problem 'find the limit of sin(x) divided by x as x approaches 0' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task ab1dda5a-a8c5-4d83-b2c3-baaaf340de03 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ab1dda5a-a8c5-4d83-b2c3-baaaf340de03 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ab1dda5a-a8c5-4d83-b2c3-baaaf340de03 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ab1dda5a-a8c5-4d83-b2c3-baaaf340de03 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ab1dda5a-a8c5-4d83-b2c3-baaaf340de03 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task ab1dda5a-a8c5-4d83-b2c3-baaaf340de03 completed by agent mac-wens-Mac-mini.local in 4677ms (13 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 13 tokens, 6051ms
INFO:spl.executor:GENERATE chain done -> @steps_text (19 chars total)
[INFO] [arm=solver] decomposed into 1 step(s):


sin(x)/x|limit(x,0)


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 27 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 139ms (0 LLM calls)
[INFO] [arm=solver][step 1/1] limit(sin(x)/x, x->0) = 1
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 2defe09b-4dba-4633-bc3b-db3ab922f448 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2defe09b-4dba-4633-bc3b-db3ab922f448 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2defe09b-4dba-4633-bc3b-db3ab922f448 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2defe09b-4dba-4633-bc3b-db3ab922f448 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2defe09b-4dba-4633-bc3b-db3ab922f448 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/2defe09b-4dba-4633-bc3b-db3ab922f448 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 2defe09b-4dba-4633-bc3b-db3ab922f448 completed by agent papa-game in 5601ms (362 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 362 tokens, 8035ms
INFO:spl.executor:GENERATE chain done -> @result (354 chars total)
INFO:spl.executor:RETURN: 354 chars | status=complete, arm=solver, backend=sympy, steps=1

Status:  complete
Output:  You are asking for the limit of the function $\frac{\sin(x)}{x}$ as $x$ approaches $0$. To find this value, we follow the exact steps computed by the symbolic engine.
First, we evaluate the expression: $\lim_{x \to 0} \frac{\sin(x)}{x}$.
The result of this calculation is exactly 1.
Therefore, the limit of $\frac{\sin(x)}{x}$ as $x$ approaches $0$ is 1.
LLM calls: 2  Latency: 14227ms
Workers: mac-wens-Mac-mini.local, papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma4-e2b-20260620-220405.md
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
[INFO] [arm=solver] Problem 'expand sin(x) as a Taylor series around x = 0, keeping terms up to degree 5' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 4163a42c-8b5d-48b5-8a83-c7d4c6600f09 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/4163a42c-8b5d-48b5-8a83-c7d4c6600f09 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/4163a42c-8b5d-48b5-8a83-c7d4c6600f09 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 4163a42c-8b5d-48b5-8a83-c7d4c6600f09 completed by agent mac-wens-Mac-mini.local in 504ms (6 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 6 tokens, 2026ms
INFO:spl.executor:GENERATE chain done -> @steps_text (13 chars total)
[INFO] [arm=solver] decomposed into 1 step(s):


sin(x)|series


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 72 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 116ms (0 LLM calls)
[INFO] [arm=solver][step 1/1] series(sin(x), x=0, deg≤5) = x**5/120 - x**3/6 + x
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 92683c1b-3181-46aa-9724-0969a85638c5 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/92683c1b-3181-46aa-9724-0969a85638c5 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/92683c1b-3181-46aa-9724-0969a85638c5 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/92683c1b-3181-46aa-9724-0969a85638c5 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/92683c1b-3181-46aa-9724-0969a85638c5 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/92683c1b-3181-46aa-9724-0969a85638c5 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/92683c1b-3181-46aa-9724-0969a85638c5 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 92683c1b-3181-46aa-9724-0969a85638c5 completed by agent mac-wens-Mac-mini.local in 8647ms (449 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 449 tokens, 10046ms
INFO:spl.executor:GENERATE chain done -> @result (374 chars total)
INFO:spl.executor:RETURN: 374 chars | status=complete, arm=solver, backend=sympy, steps=1

Status:  complete
Output:  You asked for the Taylor series expansion of $\sin(x)$ centered at $x=0$, keeping terms up to degree 5. The symbolic math engine computed this expansion step-by-step, resulting in: first, $x^5/120$; second, $-x^3/6$; and finally, $+x$. Combining these exact results gives the final Taylor series expansion for $\sin(x)$ up to degree 5: $x - \frac{x^3}{6} + \frac{x^5}{120}$.
LLM calls: 2  Latency: 12188ms
Workers: mac-wens-Mac-mini.local
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma4-e2b-20260620-220411.md
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
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sympy solver=true
[INFO] [arm=solver] Problem 'differentiate exp(x) and simplify it if necessary' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 55843cfa-1e1d-4967-ae43-cc10d38d2e61 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/55843cfa-1e1d-4967-ae43-cc10d38d2e61 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/55843cfa-1e1d-4967-ae43-cc10d38d2e61 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/55843cfa-1e1d-4967-ae43-cc10d38d2e61 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/55843cfa-1e1d-4967-ae43-cc10d38d2e61 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/55843cfa-1e1d-4967-ae43-cc10d38d2e61 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 55843cfa-1e1d-4967-ae43-cc10d38d2e61 completed by agent papa-game in 5407ms (6 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 6 tokens, 8072ms
INFO:spl.executor:GENERATE chain done -> @steps_text (11 chars total)
[INFO] [arm=solver] decomposed into 1 step(s):


exp(x)|diff


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 28 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 102ms (0 LLM calls)
[INFO] [arm=solver][step 1/1] d/dx(exp(x)) = exp(x)
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 556cf59f-4ece-468e-a87f-4e1f25d0a0f4 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/556cf59f-4ece-468e-a87f-4e1f25d0a0f4 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/556cf59f-4ece-468e-a87f-4e1f25d0a0f4 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/556cf59f-4ece-468e-a87f-4e1f25d0a0f4 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/556cf59f-4ece-468e-a87f-4e1f25d0a0f4 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/556cf59f-4ece-468e-a87f-4e1f25d0a0f4 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/556cf59f-4ece-468e-a87f-4e1f25d0a0f4 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 556cf59f-4ece-468e-a87f-4e1f25d0a0f4 completed by agent papa-game in 8986ms (383 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 383 tokens, 10044ms
INFO:spl.executor:GENERATE chain done -> @result (300 chars total)
INFO:spl.executor:RETURN: 300 chars | status=complete, arm=solver, backend=sympy, steps=1

Status:  complete
Output:  The question asks us to find the derivative of the function $e^x$. We use the standard rule for differentiation to solve this problem. Following the exact computation steps, we apply the derivative operator to $\exp(x)$, which results in $\exp(x)$. Therefore, the derivative of $e^x$ is simply $e^x$.
LLM calls: 2  Latency: 18219ms
Workers: papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma4-e2b-20260620-220405.md
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
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sage solver=true
[INFO] [arm=solver] Problem 'find the integral of sin(x) times cos(x), then simplify the result' — planning the chain (backend=sage) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 3c5721b4-1a5d-4441-a867-6b1690161ad9 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/3c5721b4-1a5d-4441-a867-6b1690161ad9 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/3c5721b4-1a5d-4441-a867-6b1690161ad9 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 3c5721b4-1a5d-4441-a867-6b1690161ad9 completed by agent papa-game in 953ms (15 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 15 tokens, 2025ms
INFO:spl.executor:GENERATE chain done -> @steps_text (37 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


sin(x)*cos(x)|integrate
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 62 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1836ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] integral of sin(x)*cos(x) dx = -1/2*cos(x)^2 + C
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 53 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 6ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] simplify(-1/2*cos(x)^2) = -1/2*cos(x)^2
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 9c2ab00d-0faf-40b4-87e2-142ce5a7f5c3 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/9c2ab00d-0faf-40b4-87e2-142ce5a7f5c3 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/9c2ab00d-0faf-40b4-87e2-142ce5a7f5c3 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/9c2ab00d-0faf-40b4-87e2-142ce5a7f5c3 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/9c2ab00d-0faf-40b4-87e2-142ce5a7f5c3 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/9c2ab00d-0faf-40b4-87e2-142ce5a7f5c3 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 9c2ab00d-0faf-40b4-87e2-142ce5a7f5c3 completed by agent papa-game in 7042ms (353 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 353 tokens, 8054ms
INFO:spl.executor:GENERATE chain done -> @result (328 chars total)
INFO:spl.executor:RETURN: 328 chars | status=complete, arm=solver, backend=sage, steps=2

Status:  complete
Output:  The problem asks us to find the integral of $\sin(x)$ times $\cos(x)$ and then simplify the result.

First, we compute the indefinite integral: $\int \sin(x)\cos(x) dx = -\frac{1}{2}\cos^2(x) + C$. Next, we simplify this expression by simplifying $-\frac{1}{2}\cos^2(x)$.

The final simplified answer is $-\frac{1}{2}\cos^2(x)$.
LLM calls: 2  Latency: 11923ms
Workers: papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma4-e2b-20260620-220423.md
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
INFO:spl.adapters.momagrid:Task 767e43ee-eceb-43d3-9b96-8354411a6c62 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/767e43ee-eceb-43d3-9b96-8354411a6c62 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/767e43ee-eceb-43d3-9b96-8354411a6c62 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/767e43ee-eceb-43d3-9b96-8354411a6c62 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/767e43ee-eceb-43d3-9b96-8354411a6c62 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/767e43ee-eceb-43d3-9b96-8354411a6c62 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/767e43ee-eceb-43d3-9b96-8354411a6c62 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/767e43ee-eceb-43d3-9b96-8354411a6c62 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/767e43ee-eceb-43d3-9b96-8354411a6c62 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/767e43ee-eceb-43d3-9b96-8354411a6c62 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 767e43ee-eceb-43d3-9b96-8354411a6c62 completed by agent mac-wens-Mac-mini.local in 13792ms (270 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 270 tokens, 16096ms
INFO:spl.executor:GENERATE chain done -> @steps_text (30 chars total)
[INFO] [arm=solver] decomposed into 1 step(s):


sin(x)**2 + cos(x)**2|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 37 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 189ms (0 LLM calls)
[INFO] [arm=solver][step 1/1] simplify(sin(x)**2 + cos(x)**2) = 1
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task db78dcea-6843-499d-8633-c796b5f600a1 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/db78dcea-6843-499d-8633-c796b5f600a1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/db78dcea-6843-499d-8633-c796b5f600a1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/db78dcea-6843-499d-8633-c796b5f600a1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/db78dcea-6843-499d-8633-c796b5f600a1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/db78dcea-6843-499d-8633-c796b5f600a1 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task db78dcea-6843-499d-8633-c796b5f600a1 completed by agent wengong in 6878ms (442 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 442 tokens, 8040ms
INFO:spl.executor:GENERATE chain done -> @result (264 chars total)
INFO:spl.executor:RETURN: 264 chars | status=complete, arm=solver, backend=sympy, steps=1

Status:  complete
Output:  To simplify the expression $\sin^2(x) + \cos^2(x)$, we use a fundamental trigonometric identity. Following the calculation steps, we simplify the expression: first, simplify $(\sin(x)^2 + \cos(x)^2)$ to $1$. Therefore, the simplified result of the expression is 1.
LLM calls: 2  Latency: 24327ms
Workers: mac-wens-Mac-mini.local, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma4-e2b-20260620-220413.md
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
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sage solver=true
[INFO] [arm=solver] Problem 'integrate the square root of (4 minus x squared)' — planning the chain (backend=sage) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 5001d7f4-d6d2-435a-9c0c-c4077d4a1c5b submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/5001d7f4-d6d2-435a-9c0c-c4077d4a1c5b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/5001d7f4-d6d2-435a-9c0c-c4077d4a1c5b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/5001d7f4-d6d2-435a-9c0c-c4077d4a1c5b "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 5001d7f4-d6d2-435a-9c0c-c4077d4a1c5b completed by agent papa-game in 1332ms (15 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 15 tokens, 4033ms
INFO:spl.executor:GENERATE chain done -> @steps_text (38 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


sqrt(4 - x**2)|integrate
PREV|simplify


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 113 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 2368ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] integral of sqrt(4 - x**2) dx = 1/2*sqrt(-x^2 + 4)*x + 2*arcsin(1/2*x) + C
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 128 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 14ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] simplify(1/2*sqrt(-x^2 + 4)*x + 2*arcsin(1/2*x)) = 1/2*sqrt(-x^2 + 4)*x + 2*arcsin(1/2*x)
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 3a90971f-de88-41a3-b66e-125bcb8a4ffc submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/3a90971f-de88-41a3-b66e-125bcb8a4ffc "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/3a90971f-de88-41a3-b66e-125bcb8a4ffc "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/3a90971f-de88-41a3-b66e-125bcb8a4ffc "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/3a90971f-de88-41a3-b66e-125bcb8a4ffc "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/3a90971f-de88-41a3-b66e-125bcb8a4ffc "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/3a90971f-de88-41a3-b66e-125bcb8a4ffc "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/3a90971f-de88-41a3-b66e-125bcb8a4ffc "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/3a90971f-de88-41a3-b66e-125bcb8a4ffc "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 3a90971f-de88-41a3-b66e-125bcb8a4ffc completed by agent mac-wens-Mac-mini.local in 10703ms (561 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 561 tokens, 14076ms
INFO:spl.executor:GENERATE chain done -> @result (342 chars total)
INFO:spl.executor:RETURN: 342 chars | status=complete, arm=solver, backend=sage, steps=2

Status:  complete
Output:  We are calculating the indefinite integral of the square root of $(4 - x^2)$. The first step of the integration process yields: $\frac{1}{2}\sqrt{-x^2 + 4}x + 2\arcsin(\frac{1}{2}x) + C$. Next, we simplify this result by applying the `simplify` function. This leads to the final answer: $\frac{1}{2}\sqrt{-x^2 + 4}x + 2\arcsin(\frac{1}{2}x)$.
LLM calls: 2  Latency: 20493ms
Workers: mac-wens-Mac-mini.local, papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma4-e2b-20260620-220420.md
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
[INFO] [arm=solver] Problem 'expand (x+1)**2, then factor the expanded form' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 09ae38c9-9841-4f22-a60f-c04a277b5601 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/09ae38c9-9841-4f22-a60f-c04a277b5601 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 09ae38c9-9841-4f22-a60f-c04a277b5601 completed by agent wengong in 54233ms (355 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 355 tokens, 56305ms
INFO:spl.executor:GENERATE chain done -> @steps_text (29 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


(x + 1)**2|expand
PREV|factor


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 50 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 165ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] expand((x + 1)**2) = x**2 + 2*x + 1
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 46 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] factor(x**2 + 2*x + 1) = (x + 1)**2
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 66188941-dd15-4a16-8167-3617a34eed4b submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/66188941-dd15-4a16-8167-3617a34eed4b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/66188941-dd15-4a16-8167-3617a34eed4b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/66188941-dd15-4a16-8167-3617a34eed4b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/66188941-dd15-4a16-8167-3617a34eed4b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/66188941-dd15-4a16-8167-3617a34eed4b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/66188941-dd15-4a16-8167-3617a34eed4b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/66188941-dd15-4a16-8167-3617a34eed4b "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 66188941-dd15-4a16-8167-3617a34eed4b completed by agent papa-game in 10059ms (496 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 496 tokens, 12045ms
INFO:spl.executor:GENERATE chain done -> @result (301 chars total)
INFO:spl.executor:RETURN: 301 chars | status=complete, arm=solver, backend=sympy, steps=2

Status:  complete
Output:  This problem asks us to first expand the expression $(x+1)^2$, and then factor the resulting polynomial. First, we expand the expression: $\text{expand}((x + 1)^2) = x^2 + 2x + 1$. Next, we factor this expanded form: $\text{factor}(x^2 + 2x + 1) = (x + 1)^2$. Therefore, the final answer is $(x+1)^2$.
LLM calls: 2  Latency: 68517ms
Workers: papa-game, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma4-e2b-20260620-220334.md
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
INFO:spl.adapters.momagrid:Task e9d5c378-7f4f-486d-86e6-94cc5719f1c7 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/e9d5c378-7f4f-486d-86e6-94cc5719f1c7 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/e9d5c378-7f4f-486d-86e6-94cc5719f1c7 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/e9d5c378-7f4f-486d-86e6-94cc5719f1c7 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/e9d5c378-7f4f-486d-86e6-94cc5719f1c7 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task e9d5c378-7f4f-486d-86e6-94cc5719f1c7 completed by agent papa-game in 4007ms (230 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 230 tokens, 6046ms
INFO:spl.executor:GENERATE chain done -> @steps_text (35 chars total)
[INFO] [arm=solver] decomposed into 1 step(s):


[x + y - 5, x - y - 1]|solve_system


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 80 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1821ms (0 LLM calls)
[INFO] [arm=solver][step 1/1] solve_system([x + y - 5, x - y - 1]) = [
[x == 3, y == 2]
]
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task b400bbac-037e-4a39-a86b-70525f3aa5e9 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/b400bbac-037e-4a39-a86b-70525f3aa5e9 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/b400bbac-037e-4a39-a86b-70525f3aa5e9 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/b400bbac-037e-4a39-a86b-70525f3aa5e9 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/b400bbac-037e-4a39-a86b-70525f3aa5e9 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/b400bbac-037e-4a39-a86b-70525f3aa5e9 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/b400bbac-037e-4a39-a86b-70525f3aa5e9 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/b400bbac-037e-4a39-a86b-70525f3aa5e9 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task b400bbac-037e-4a39-a86b-70525f3aa5e9 completed by agent wengong in 11800ms (490 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 490 tokens, 12065ms
INFO:spl.executor:GENERATE chain done -> @result (393 chars total)
INFO:spl.executor:RETURN: 393 chars | status=complete, arm=solver, backend=sage, steps=1

Status:  complete
Output:  This problem asks us to find the values of $x$ and $y$ that satisfy the system of equations $x + y = 5$ and $x - y = 1$. The symbolic engine solved this by calculating:
1. `solve_system([x + y - 5, x - y - 1])` which results in finding the values for $x$ and $y$.
2. This process leads to the solution: $[x == 3, y == 2]$.
Therefore, the solution to the system of equations is $x=3$ and $y=2$.
LLM calls: 2  Latency: 19935ms
Workers: papa-game, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma4-e2b-20260620-220424.md
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
[INFO] [neurosymbolic_solver] host=mac-wens-Mac-mini.local backend=sympy solver=true
[INFO] [arm=solver] Problem 'differentiate 3*x**3-x, then factor if needed, finally solve for x' — planning the chain (backend=sympy) ...
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 340b2bb7-00c3-4762-9a6f-10748822511b submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/340b2bb7-00c3-4762-9a6f-10748822511b "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 340b2bb7-00c3-4762-9a6f-10748822511b completed by agent wengong in 48744ms (1213 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 1213 tokens, 52307ms
INFO:spl.executor:GENERATE chain done -> @steps_text (38 chars total)
[INFO] [arm=solver] decomposed into 3 step(s):


3*x**3 - x|diff
PREV|factor
PREV|solve


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 40 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 156ms (0 LLM calls)
[INFO] [arm=solver][step 1/3] d/dx(3*x**3 - x) = 9*x**2 - 1
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 60 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 2ms (0 LLM calls)
[INFO] [arm=solver][step 2/3] factor(9*x**2 - 1) = (3*x - 1)*(3*x + 1)
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 61 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 3/3] solve((3*x - 1)*(3*x + 1) = 0) -> x = [-1/3, 1/3]
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 704c0f16-881c-4022-943d-7491638ac50b submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/704c0f16-881c-4022-943d-7491638ac50b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/704c0f16-881c-4022-943d-7491638ac50b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/704c0f16-881c-4022-943d-7491638ac50b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/704c0f16-881c-4022-943d-7491638ac50b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/704c0f16-881c-4022-943d-7491638ac50b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/704c0f16-881c-4022-943d-7491638ac50b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/704c0f16-881c-4022-943d-7491638ac50b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/704c0f16-881c-4022-943d-7491638ac50b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/704c0f16-881c-4022-943d-7491638ac50b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/704c0f16-881c-4022-943d-7491638ac50b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/704c0f16-881c-4022-943d-7491638ac50b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/704c0f16-881c-4022-943d-7491638ac50b "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/704c0f16-881c-4022-943d-7491638ac50b "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 704c0f16-881c-4022-943d-7491638ac50b completed by agent mac-wens-Mac-mini.local in 21613ms (580 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 580 tokens, 24091ms
INFO:spl.executor:GENERATE chain done -> @result (327 chars total)
INFO:spl.executor:RETURN: 327 chars | status=complete, arm=solver, backend=sympy, steps=3

Status:  complete
Output:  This problem asks us to first find the derivative of $3x^3 - x$, then factor that result, and finally solve the resulting equation for $x$. Following these steps, we found the following results: 1. Differentiation yields $9x^2 - 1$; 2. Factoring gives $(3x - 1)(3x + 1)$; and 3. Solving the equation leads to $x = [-1/3, 1/3]$.
LLM calls: 2  Latency: 76558ms
Workers: mac-wens-Mac-mini.local, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma4-e2b-20260620-220334.md
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
INFO:spl.adapters.momagrid:Task ca9f7491-fe52-4d70-aaf9-b021aad24339 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ca9f7491-fe52-4d70-aaf9-b021aad24339 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ca9f7491-fe52-4d70-aaf9-b021aad24339 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ca9f7491-fe52-4d70-aaf9-b021aad24339 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ca9f7491-fe52-4d70-aaf9-b021aad24339 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ca9f7491-fe52-4d70-aaf9-b021aad24339 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task ca9f7491-fe52-4d70-aaf9-b021aad24339 completed by agent wengong in 4609ms (9 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 9 tokens, 8049ms
INFO:spl.executor:GENERATE chain done -> @steps_text (17 chars total)
[INFO] [arm=solver] decomposed into 1 step(s):


exp(-2*t)|laplace


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 50 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1946ms (0 LLM calls)
[INFO] [arm=solver][step 1/1] laplace_transform(exp(-2*t)) = 1/(s + 2)
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 57e25460-d2b8-499b-ad1c-8961ba00c0e4 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/57e25460-d2b8-499b-ad1c-8961ba00c0e4 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/57e25460-d2b8-499b-ad1c-8961ba00c0e4 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/57e25460-d2b8-499b-ad1c-8961ba00c0e4 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/57e25460-d2b8-499b-ad1c-8961ba00c0e4 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/57e25460-d2b8-499b-ad1c-8961ba00c0e4 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/57e25460-d2b8-499b-ad1c-8961ba00c0e4 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 57e25460-d2b8-499b-ad1c-8961ba00c0e4 completed by agent papa-game in 6075ms (394 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 394 tokens, 10062ms
INFO:spl.executor:GENERATE chain done -> @result (289 chars total)
INFO:spl.executor:RETURN: 289 chars | status=complete, arm=solver, backend=sage, steps=1

Status:  complete
Output:  We are asked to find the Laplace transform of the function $e^{-2t}$.

Following the calculation steps, we apply the Laplace transform operator to the expression:
1. $\text{laplace\_transform}(\exp(-2t)) = \frac{1}{s + 2}$

Therefore, the Laplace transform of $e^{-2t}$ is $\frac{1}{s+2}$.
LLM calls: 2  Latency: 20058ms
Workers: papa-game, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma4-e2b-20260620-220438.md
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
INFO:spl.adapters.momagrid:Task 453dd9cf-223e-45a3-b51b-10a3cd63b1de submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/453dd9cf-223e-45a3-b51b-10a3cd63b1de "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/453dd9cf-223e-45a3-b51b-10a3cd63b1de "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/453dd9cf-223e-45a3-b51b-10a3cd63b1de "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/453dd9cf-223e-45a3-b51b-10a3cd63b1de "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/453dd9cf-223e-45a3-b51b-10a3cd63b1de "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/453dd9cf-223e-45a3-b51b-10a3cd63b1de "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 453dd9cf-223e-45a3-b51b-10a3cd63b1de completed by agent papa-game in 8107ms (264 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 264 tokens, 10070ms
INFO:spl.executor:GENERATE chain done -> @steps_text (28 chars total)
[INFO] [arm=solver] decomposed into 1 step(s):


[[1, 2], [3, 4]]|eigenvalues


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 115 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1994ms (0 LLM calls)
[INFO] [arm=solver][step 1/1] eigenvalues([[1, 2], [3, 4]]) = [-1/2*sqrt(33) + 5/2, 1/2*sqrt(33) + 5/2]
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task cb63556d-066c-4351-9571-894dda30a000 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/cb63556d-066c-4351-9571-894dda30a000 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/cb63556d-066c-4351-9571-894dda30a000 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/cb63556d-066c-4351-9571-894dda30a000 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/cb63556d-066c-4351-9571-894dda30a000 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/cb63556d-066c-4351-9571-894dda30a000 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/cb63556d-066c-4351-9571-894dda30a000 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/cb63556d-066c-4351-9571-894dda30a000 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task cb63556d-066c-4351-9571-894dda30a000 completed by agent wengong in 9366ms (487 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 487 tokens, 12059ms
INFO:spl.executor:GENERATE chain done -> @result (432 chars total)
INFO:spl.executor:RETURN: 432 chars | status=complete, arm=solver, backend=sage, steps=1

Status:  complete
Output:  We are finding the eigenvalues for the 2 by 2 matrix whose rows are [1, 2] and [3, 4]. The symbolic engine calculated this process in exact steps: first, it determined the values associated with the characteristic equation. Next, it provided the two individual results derived from that calculation. Therefore, the eigenvalues of the matrix are $\left[-\frac{1}{2}\sqrt{33} + \frac{5}{2}, \frac{1}{2}\sqrt{33} + \frac{5}{2}\right]$.
LLM calls: 2  Latency: 24125ms
Workers: papa-game, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma4-e2b-20260620-220436.md
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
INFO:spl.adapters.momagrid:Task b33542ff-231f-4ca7-a9e5-b38f9ea6a45e submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/b33542ff-231f-4ca7-a9e5-b38f9ea6a45e "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/b33542ff-231f-4ca7-a9e5-b38f9ea6a45e "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/b33542ff-231f-4ca7-a9e5-b38f9ea6a45e "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/b33542ff-231f-4ca7-a9e5-b38f9ea6a45e "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task b33542ff-231f-4ca7-a9e5-b38f9ea6a45e completed by agent wengong in 4178ms (16 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 16 tokens, 6038ms
INFO:spl.executor:GENERATE chain done -> @steps_text (24 chars total)
[INFO] [arm=solver] decomposed into 1 step(s):


1/n**2|summation(n,1,oo)


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 47 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1711ms (0 LLM calls)
[INFO] [arm=solver][step 1/1] sum(1/n**2, n=1..+Infinity) = 1/6*pi^2
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 40101540-5d38-46ad-9da9-dbefe631f971 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/40101540-5d38-46ad-9da9-dbefe631f971 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/40101540-5d38-46ad-9da9-dbefe631f971 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/40101540-5d38-46ad-9da9-dbefe631f971 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/40101540-5d38-46ad-9da9-dbefe631f971 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/40101540-5d38-46ad-9da9-dbefe631f971 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/40101540-5d38-46ad-9da9-dbefe631f971 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 40101540-5d38-46ad-9da9-dbefe631f971 completed by agent mac-wens-Mac-mini.local in 7840ms (403 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 403 tokens, 10056ms
INFO:spl.executor:GENERATE chain done -> @result (430 chars total)
INFO:spl.executor:RETURN: 430 chars | status=complete, arm=solver, backend=sage, steps=1

Status:  complete
Output:  The problem asks for the symbolic sum of the infinite series where you add the reciprocal of each number squared, starting from $n=1$. Following the computed steps exactly, we find that summing $\frac{1}{n^2}$ from $n=1$ to infinity leads directly to the result. The first step shows that this specific sum is equal to $\frac{1}{6}\pi^2$. Therefore, the symbolic sum of $\frac{1}{n^2}$ from $n=1$ to infinity is $\frac{\pi^2}{6}$.
LLM calls: 2  Latency: 17806ms
Workers: mac-wens-Mac-mini.local, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma4-e2b-20260620-220443.md
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
INFO:spl.adapters.momagrid:Task 7eee5cd2-376e-4f43-a807-aeab0ac57f45 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/7eee5cd2-376e-4f43-a807-aeab0ac57f45 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/7eee5cd2-376e-4f43-a807-aeab0ac57f45 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/7eee5cd2-376e-4f43-a807-aeab0ac57f45 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/7eee5cd2-376e-4f43-a807-aeab0ac57f45 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/7eee5cd2-376e-4f43-a807-aeab0ac57f45 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/7eee5cd2-376e-4f43-a807-aeab0ac57f45 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 7eee5cd2-376e-4f43-a807-aeab0ac57f45 completed by agent mac-wens-Mac-mini.local in 8076ms (19 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 19 tokens, 10065ms
INFO:spl.executor:GENERATE chain done -> @steps_text (37 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


y(x).diff(x)|ode_solve
PREV|ode_solve


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 43 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1415ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] dsolve(y(x).diff(x) = 0) -> Eq(y(x), C1)
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 37 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 0ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] C1 (already solved — pass-through)
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 6586401b-5cbb-4650-b09e-16bf2db0e0aa submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/6586401b-5cbb-4650-b09e-16bf2db0e0aa "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/6586401b-5cbb-4650-b09e-16bf2db0e0aa "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/6586401b-5cbb-4650-b09e-16bf2db0e0aa "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/6586401b-5cbb-4650-b09e-16bf2db0e0aa "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/6586401b-5cbb-4650-b09e-16bf2db0e0aa "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/6586401b-5cbb-4650-b09e-16bf2db0e0aa "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/6586401b-5cbb-4650-b09e-16bf2db0e0aa "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/6586401b-5cbb-4650-b09e-16bf2db0e0aa "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 6586401b-5cbb-4650-b09e-16bf2db0e0aa completed by agent wengong in 12157ms (480 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 480 tokens, 14059ms
INFO:spl.executor:GENERATE chain done -> @result (516 chars total)
INFO:spl.executor:RETURN: 516 chars | status=complete, arm=solver, backend=sage, steps=2

Status:  complete
Output:  This problem asks us to solve the differential equation $y'(x) = y(x)$ given the initial condition $y(0) = 1$. The symbolic math engine finds the general solution by solving the homogeneous equation first. Step 1, `dsolve(y(x).diff(x) = 0)`, results in the general solution form $\text{Eq}(y(x), C1)$. Since this step already provides the complete solution structure, the subsequent step simply passes through the result. Therefore, applying the initial condition $y(0)=1$ gives us the specific answer: $y(x) = e^x$.
LLM calls: 2  Latency: 25541ms
Workers: mac-wens-Mac-mini.local, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma4-e2b-20260620-220441.md
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
INFO:spl.adapters.momagrid:Task f841ed60-d7d7-43bc-ae8f-362df8efe188 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f841ed60-d7d7-43bc-ae8f-362df8efe188 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f841ed60-d7d7-43bc-ae8f-362df8efe188 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f841ed60-d7d7-43bc-ae8f-362df8efe188 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f841ed60-d7d7-43bc-ae8f-362df8efe188 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/f841ed60-d7d7-43bc-ae8f-362df8efe188 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task f841ed60-d7d7-43bc-ae8f-362df8efe188 completed by agent wengong in 6460ms (298 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 298 tokens, 8039ms
INFO:spl.executor:GENERATE chain done -> @steps_text (14 chars total)
[INFO] [arm=solver] decomposed into 1 step(s):


x**4 - 1|solve


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 56 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1817ms (0 LLM calls)
[INFO] [arm=solver][step 1/1] solve(x**4 - 1 = 0) -> x = [I, -1, -I, 1]
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task ad474fed-9544-4d69-b2ca-5feb8b59e8c1 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ad474fed-9544-4d69-b2ca-5feb8b59e8c1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ad474fed-9544-4d69-b2ca-5feb8b59e8c1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ad474fed-9544-4d69-b2ca-5feb8b59e8c1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ad474fed-9544-4d69-b2ca-5feb8b59e8c1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ad474fed-9544-4d69-b2ca-5feb8b59e8c1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ad474fed-9544-4d69-b2ca-5feb8b59e8c1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ad474fed-9544-4d69-b2ca-5feb8b59e8c1 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/ad474fed-9544-4d69-b2ca-5feb8b59e8c1 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task ad474fed-9544-4d69-b2ca-5feb8b59e8c1 completed by agent mac-wens-Mac-mini.local in 12380ms (459 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 459 tokens, 14078ms
INFO:spl.executor:GENERATE chain done -> @result (345 chars total)
INFO:spl.executor:RETURN: 345 chars | status=complete, arm=solver, backend=sage, steps=1

Status:  complete
Output:  We need to find all four roots of the equation $x^4 - 1 = 0$ and express them in simplified form. We start by solving the polynomial equation using symbolic methods. The engine calculated this process as follows: solving $x^4 - 1 = 0$ yields the roots $x = [I, -1, -I, 1]$. Therefore, the four roots of the equation are $1$, $-1$, $I$, and $-I$.
LLM calls: 2  Latency: 23935ms
Workers: mac-wens-Mac-mini.local, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma4-e2b-20260620-220444.md
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
INFO:spl.adapters.momagrid:Task 6c22c52f-835a-498a-b5b1-495413e89c11 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/6c22c52f-835a-498a-b5b1-495413e89c11 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/6c22c52f-835a-498a-b5b1-495413e89c11 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/6c22c52f-835a-498a-b5b1-495413e89c11 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/6c22c52f-835a-498a-b5b1-495413e89c11 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 6c22c52f-835a-498a-b5b1-495413e89c11 completed by agent papa-game in 4687ms (34 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 34 tokens, 6036ms
INFO:spl.executor:GENERATE chain done -> @steps_text (50 chars total)
[INFO] [arm=solver] decomposed into 1 step(s):


y(x).diff(x,2) - 3*y(x).diff(x) + 2*y(x)|ode_solve


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 113 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1704ms (0 LLM calls)
[INFO] [arm=solver][step 1/1] dsolve(y(x).diff(x,2) - 3*y(x).diff(x) + 2*y(x) = 0) -> Eq(y(x), (C1 + C2*exp(x))*exp(x))
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 25f6da6c-4f74-4d87-afe3-618e2e0a762f submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/25f6da6c-4f74-4d87-afe3-618e2e0a762f "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/25f6da6c-4f74-4d87-afe3-618e2e0a762f "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/25f6da6c-4f74-4d87-afe3-618e2e0a762f "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/25f6da6c-4f74-4d87-afe3-618e2e0a762f "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/25f6da6c-4f74-4d87-afe3-618e2e0a762f "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/25f6da6c-4f74-4d87-afe3-618e2e0a762f "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/25f6da6c-4f74-4d87-afe3-618e2e0a762f "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/25f6da6c-4f74-4d87-afe3-618e2e0a762f "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/25f6da6c-4f74-4d87-afe3-618e2e0a762f "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 25f6da6c-4f74-4d87-afe3-618e2e0a762f completed by agent wengong in 13684ms (540 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 540 tokens, 16075ms
INFO:spl.executor:GENERATE chain done -> @result (407 chars total)
INFO:spl.executor:RETURN: 407 chars | status=complete, arm=solver, backend=sage, steps=1

Status:  complete
Output:  This question asks for the general solution to the second-order linear homogeneous differential equation $y''(x) - 3y'(x) + 2y(x) = 0$. We use the `dsolve` function to find this solution. Following the computation, the symbolic engine determined that the general solution is given by $y(x) = (C_1 + C_2 e^x)e^x$. Therefore, the general solution to the differential equation is $y(x) = C_1 e^x + C_2 e^{2x}$.
LLM calls: 2  Latency: 23818ms
Workers: papa-game, wengong
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma4-e2b-20260620-220451.md
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
INFO:spl.adapters.momagrid:Task fbdcd946-6b56-44f7-8f1c-7e2b5814d901 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/fbdcd946-6b56-44f7-8f1c-7e2b5814d901 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/fbdcd946-6b56-44f7-8f1c-7e2b5814d901 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/fbdcd946-6b56-44f7-8f1c-7e2b5814d901 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/fbdcd946-6b56-44f7-8f1c-7e2b5814d901 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/fbdcd946-6b56-44f7-8f1c-7e2b5814d901 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/fbdcd946-6b56-44f7-8f1c-7e2b5814d901 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task fbdcd946-6b56-44f7-8f1c-7e2b5814d901 completed by agent papa-game in 8439ms (526 tokens)
INFO:spl.executor:GENERATE segment 1 (decompose_problem) -> 526 tokens, 10051ms
INFO:spl.executor:GENERATE chain done -> @steps_text (43 chars total)
[INFO] [arm=solver] decomposed into 2 step(s):


s / (s**2 + 4)|inverse_laplace
PREV|laplace


INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 61 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1706ms (0 LLM calls)
[INFO] [arm=solver][step 1/2] inverse_laplace_transform(s / (s**2 + 4)) = cos(2*t)
INFO:spl.composer:CALL solve_chain_step(['step', 'running_expression', 'backend']) INTO @step_summary
INFO:spl.executor:RETURN: 53 chars | none
INFO:spl.composer:CALL solve_chain_step completed: status=complete in 1ms (0 LLM calls)
[INFO] [arm=solver][step 2/2] laplace_transform(cos(2*t)) = s/(s^2 + 4)
INFO:httpx:HTTP Request: POST http://192.168.0.170:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 0d2effd6-d4fd-49e8-b82e-22b9e812cba7 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/0d2effd6-d4fd-49e8-b82e-22b9e812cba7 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/0d2effd6-d4fd-49e8-b82e-22b9e812cba7 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/0d2effd6-d4fd-49e8-b82e-22b9e812cba7 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/0d2effd6-d4fd-49e8-b82e-22b9e812cba7 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/0d2effd6-d4fd-49e8-b82e-22b9e812cba7 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.170:9000/tasks/0d2effd6-d4fd-49e8-b82e-22b9e812cba7 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 0d2effd6-d4fd-49e8-b82e-22b9e812cba7 completed by agent papa-game in 7347ms (481 tokens)
INFO:spl.executor:GENERATE segment 1 (explain_chain) -> 481 tokens, 10065ms
INFO:spl.executor:GENERATE chain done -> @result (440 chars total)
INFO:spl.executor:RETURN: 440 chars | status=complete, arm=solver, backend=sage, steps=2

Status:  complete
Output:  The problem asks us to find the inverse Laplace transform of $\frac{s}{s^2 + 4}$ and then verify this result by taking the Laplace transform of that expression. First, computing the inverse yields $\cos(2t)$. Next, applying the Laplace transform to this result gives $\frac{s}{s^2 + 4}$. This confirms the correctness of the chain. The final verification shows that performing these operations results in the original function, $s/(s^2+4)$.
LLM calls: 2  Latency: 21824ms
Workers: papa-game
Log:     /Users/mac-wen/.spl/logs/symbolic_math-momagrid-gemma4-e2b-20260620-220458.md
```

