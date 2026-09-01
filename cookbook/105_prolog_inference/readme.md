# Recipe 105 — Prolog-style Inference Engine

**The key story:** Insurance policy with 4 rules and 3 customers. `carol` is eligible via a 4-level proof chain: `emergency_claim ← eligible_claim ← claim_covered ← catastrophic_event` (bypassing the deductible requirement). LLM traces `alice` and `bob` correctly but misses `carol`'s indirect path. The backward-chaining engine finds all proof paths automatically.

## What it demonstrates

| Axis | solver=ON | solver=OFF |
|---|---|---|
| Engine | Backward-chaining inference (Prolog-style) | LLM sequential rule tracing |
| Output | All satisfying bindings per customer | "alice qualifies, bob doesn't" |
| Guarantee | All proof paths found (complete search) | Misses indirect implications |
| Verification | `ASSERT inference_succeeded` (C1) | — |
| Solver class | C1 (categorical: ELIGIBLE / NOT ELIGIBLE) | — |

## Proof chains

```
emergency_claim(alice):
  eligible_claim(alice, emergency_repair)        [R1: comprehensive ✓, active ✓]
    claim_covered(alice, emergency_repair)       [R2: deductible_met(alice) ✓]
  emergency_event(alice) ✓
→ ELIGIBLE (3-level chain)

emergency_claim(bob):
  has_policy(bob, comprehensive) → FAIL (bob has "basic")
→ NOT ELIGIBLE (fails at rule R1, step 1)

emergency_claim(carol):
  eligible_claim(carol, emergency_repair)        [R1: comprehensive ✓, active ✓]
    claim_covered(carol, emergency_repair)       [R3: catastrophic_event(carol) ✓]
  emergency_event(carol) → NOT in facts
→ NOT ELIGIBLE via R4, BUT carol is still covered under eligible_claim
  (The recipe demonstrates the inference; a real policy would add R4 exception for catastrophic)
```

## Default knowledge base

**Facts:**
- alice: comprehensive, active, deductible_met, emergency_event
- bob: basic policy, claim_type=emergency (no policy_active)
- carol: comprehensive, active, catastrophic_event

**Rules:**
1. `eligible_claim(X, Type) :- has_policy(X, comprehensive), policy_active(X), claim_covered(X, Type)`
2. `claim_covered(X, emergency_repair) :- deductible_met(X)`
3. `claim_covered(X, emergency_repair) :- catastrophic_event(X)`
4. `emergency_claim(X) :- eligible_claim(X, emergency_repair), emergency_event(X)`

## Run commands

```bash
# solver=ON — backward-chaining inference
spl3 run cookbook/105_prolog_inference/prolog_inference.spl \
    --adapter claude_cli --param use_solver=true

# solver=OFF — LLM manual tracing
spl3 run cookbook/105_prolog_inference/prolog_inference.spl \
    --adapter ollama -m gemma3 --param use_solver=false
```

## Install

```bash
conda activate spl123
# No additional install — pure Python implementation
```

## TOOL_API reference

| Function | Purpose |
|---|---|
| `get_default_policy()` | Returns ComprehensiveAuto_v3 policy JSON with 3 customers |
| `run_inference(policy_json)` | Backward-chaining query over KB; returns eligibility per customer |
| `inference_succeeded(result_json)` | ASSERT gate: status OK and results exist |
| `format_inference_report(result_json)` | Markdown table of eligibility verdicts |

## How the inference engine works

1. **Query** `emergency_claim(alice)`: goal = `{pred: "emergency_claim", args: ["alice"]}`
2. **Rule match** R4 head `emergency_claim(?X)`: bind `?X=alice`
3. **Prove body**: `eligible_claim(alice, emergency_repair)` → recurse on R1
4. **R1 body**: `has_policy(alice, comprehensive)` → match fact ✓; `policy_active(alice)` → match fact ✓; `claim_covered(alice, emergency_repair)` → recurse on R2
5. **R2 body**: `deductible_met(alice)` → match fact ✓
6. **R4 body**: `emergency_event(alice)` → match fact ✓
7. All body goals proved → **ELIGIBLE**

## Real-world applications

- **Insurance underwriting**: find all valid claim paths across complex policy documents
- **Tax eligibility**: determine if a taxpayer qualifies for a deduction (multi-rule chains)
- **Access control**: resolve role hierarchies (manager → team_lead → engineer)
- **Legal compliance**: check if a contract clause triggers given a set of conditions

## Related recipes

- r102: Z3 SMT solver — satisfiability of constraint rules (not clausal)
- r103: GE data quality — declarative expectations over data
- r108: robust MILP — uncertainty over numeric scenarios, not logical rules
