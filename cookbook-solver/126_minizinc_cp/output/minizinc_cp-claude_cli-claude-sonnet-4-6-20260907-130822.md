# SPL Run: minizinc_cp

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 329 in / 503 out
- **Latency:** 179333ms
- **Timestamp:** 2026-09-07 13:08:22

## Output

```output
=== MiniZinc CP — Nurse Scheduling (r126) | solver=OFF ===

── LLM Schedule ─────────────────────────────────────────────
## 7-Day Nurse Schedule

| Nurse | Mon | Tue | Wed | Thu | Fri | Sat | Sun | Days |
|-------|-----|-----|-----|-----|-----|-----|-----|------|
| **N1** (sr) | M | M | M | M | M | Off | Off | 5 |
| **N2** (sr) | A | A | A | Off | Off | M | M | 5 |
| N3 | M | M | M | M | M | Off | Off | 5 |
| N4 | N | N | Off | A | Off | A | N | 5 |
| N5 | N | Off | N | N | Off | N | A | 5 |
| N6 | Off | N | Off | A | N | A | M | 5 |
| N7 | A | A | Off | Off | A | M | A | 5 |
| N8 | A | A | A | A | A | Off | Off | 5 |

M = Morning (06–14) · A = Afternoon (14–22) · N = Night (22–06)

---

## Hard Constraint Verification

**1. Morning ≥ 2 nurses, ≥ 1 senior**

| Day | Nurses | Senior? |
|-----|--------|---------|
| Mon | N1, N3 | N1 ✓ |
| Tue | N1, N3 | N1 ✓ |
| Wed | N1, N3 | N1 ✓ |
| Thu | N1, N3 | N1 ✓ |
| Fri | N1, N3 | N1 ✓ |
| Sat | N2, N7 | N2 ✓ |
| Sun | N2, N6 | N2 ✓ |

**2. Afternoon ≥ 2 nurses** — Mon: N2/N7/N8(3) · Tue: N2/N7/N8(3) · Wed: N2/N8(2) · Thu: N4/N6/N8(3) · Fri: N7/N8(2) · Sat: N4/N6(2) · Sun: N5/N7(2) — all ✓

**3. Night ≥ 1 nurse** — Mon: N4/N5(2) · Tue: N4/N6(2) · Wed: N5(1) · Thu: N5(1) · Fri: N6(1) · Sat: N5(1) · Sun: N4(1) — all ✓

**4. ≤ 5 days/week** — every nurse works exactly 5 days ✓

**5. Night-D → no Morning-D+1 rest rule**

| Nurse | Night shift | Next morning | Result |
|-------|------------|--------------|--------|
| N4 | Mon N | Tue = N (not M) | ✓ |
| N4 | Tue N | Wed = Off | ✓ |
| N4 | Sun N | Mon (next week, out of scope) | ✓ |
| N5 | Mon N | Tue = Off | ✓ |
| N5 | Wed N | Thu = N (not M) | ✓ |
| N5 | Thu N | Fri = Off | ✓ |
| N5 | Sat N | Sun = A (not M) | ✓ |
| N6 | Tue N | Wed = Off | ✓ |
| N6 | Fri N | Sat = A (not M) | ✓ |

---

## Soft Preference Satisfaction — 3/3

| Preference | Result |
|-----------|--------|
| N3 prefers mornings | Morning every working day (Mon–Fri) — **fully satisfied** |
| N7 avoids nights | M or A only, zero night shifts — **fully satisfied** |
| N8 consecutive days off | Off Sat + Sun (two consecutive) — **fully satisfied** |

── Constraint Check ─────────────────────────────────────────
Estimated night→morning violations: 0

Note: LLM "soft reasoning" often misses hard constraint interactions.
Run --param use_solver=true for MiniZinc CP with guaranteed constraint satisfaction.
```
