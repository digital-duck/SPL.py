# Recipe-77 Momagrid experiment run 20260620-212019

DB source: `exp-momagrid-20260620-212019`
Momagrid Hub: http://localhost:9000
Workers: 6


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
