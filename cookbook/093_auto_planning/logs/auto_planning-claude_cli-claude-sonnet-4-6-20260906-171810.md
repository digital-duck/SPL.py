# SPL Run: auto_planning

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 581 in / 219 out
- **Latency:** 12947ms
- **Timestamp:** 2026-09-06 17:18:10

## Output

```output
# Automated Planning Report

**Problem:** Truck t1 starts at A. Package p1 starts at A, package p2 starts at B. Deliver BOTH packages to location C using t1 (t1 can carry any number of packages at once; it can drive directly between any two locations).

**Validator status (VAL-style):** `OK`
**Plan length:** `6 steps`
**Final package locations:** `{'p1': 'C', 'p2': 'C'}`
**Round-trip check:** `match`

## Interpretation

**Goal:** Deliver packages p1 (starting at A) and p2 (starting at B) to location C using truck t1 (starting at A).

**Plan:** The validated plan completes in **6 steps**: load p1 at A, drive to B, load p2, drive to C, unload p1, unload p2.

**Why preconditions matter:** Each action requires specific world-state conditions (truck location, package location, load status) to hold before execution — a plan that looks correct on paper can silently fail if any precondition is violated at runtime.

Final answer: 6

## Proposed Plan (LLM-generated, JSON)

```json
[{"action": "load", "truck": "t1", "pkg": "p1", "loc": "A"}, {"action": "drive", "truck": "t1", "from": "A", "to": "B"}, {"action": "load", "truck": "t1", "pkg": "p2", "loc": "B"}, {"action": "drive", "truck": "t1", "from": "B", "to": "C"}, {"action": "unload", "truck": "t1", "pkg": "p1", "loc": "C"}, {"action": "unload", "truck": "t1", "pkg": "p2", "loc": "C"}]
```
```
