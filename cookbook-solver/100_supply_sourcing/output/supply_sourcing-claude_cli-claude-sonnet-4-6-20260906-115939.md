# SPL Run: supply_sourcing

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 747 in / 213 out
- **Latency:** 44960ms
- **Timestamp:** 2026-09-06 11:59:39

## Output

```output
=== Supply Sourcing (solver=OFF / LLM heuristic) ===

Problem:
A manufacturer needs 1000 units from 3 suppliers. S1: $10/unit, 95% fill rate, capacity 400 units. S2: $7/unit, 80% fill rate, capacity 500 units. S3: $5/unit, 60% fill rate, capacity 400 units. Find allocations that minimize cost and maximize fill rate.

LLM Allocation:
```json
{
  "cost": 6500.0,
  "fill_rate": 0.735,
  "allocation": {"S1": 100, "S2": 500, "S3": 400},
  "reasoning": "Allocate greedily by fill-rate-per-dollar ratio (S3=0.120, S2=0.114, S1=0.095), filling highest-value suppliers first to minimize cost while maintaining balanced fill-rate coverage."
}
```

Extracted Solution (JSON):
{"cost": 6500.0, "fill_rate": 0.735, "allocation": {"S1": 100, "S2": 500, "S3": 400}, "reasoning": "Allocate greedily by fill-rate-per-dollar ratio (S3=0.120, S2=0.114, S1=0.095), filling highest-value suppliers first to minimize cost while maintaining balanced fill-rate coverage."}

Verification:
{"verdict": "PASS", "recomputed_cost": 6500.0, "recomputed_fill_rate": 0.735, "notes": "all checks passed"}

LLM calls: 3
```
