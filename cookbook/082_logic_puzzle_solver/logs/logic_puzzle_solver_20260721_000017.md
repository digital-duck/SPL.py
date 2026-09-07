INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/82_logic_puzzle_solver/logic_puzzle_solver.spl
Registry: ['logic_puzzle_solver']
Running workflow: logic_puzzle_solver(['model'])
[INFO] [logic_puzzle_solver] start run_id=2026-07-21_00-01-54 solver=true
[INFO] [arm=solver] Stage 1 — LLM formulation + CSP solve
INFO:spl.executor:GENERATE segment 1 (formulate_csp_code) -> 438 tokens, 16585ms
INFO:spl.executor:GENERATE chain done -> @code (1753 chars total)
[INFO] [arm=solver] attempt 1: status=Unique
[INFO] [logic_puzzle_solver] Stage 2 — ASSERT gate (status=Unique)
INFO:spl.executor:ASSERT (tools-eval) is_unique('{"status": "Unique", "n_solutions": 1, "answer": "Dane", "houses": {"1": {"color": "Green", "nationality": "Dane", "beverage": "Coffee"}, "2": {"color": "Blue", "nationality": "Swede", "beverage": "Tea"}, "3": {"color": "Red", "nationality": "Brit", "beverage": "Milk"}}}') -> True
[INFO] [logic_puzzle_solver] ASSERT passed — solver confirmed a unique solution
INFO:spl.executor:GENERATE segment 1 (interpret_csp_result) -> 77 tokens, 4009ms
INFO:spl.executor:GENERATE chain done -> @narrative (309 chars total)
[INFO] [logic_puzzle_solver] round-trip check: match
[INFO] [logic_puzzle_solver] done — report -> /home/gongai/projects/digital-duck/SPL.py/cookbook/82_logic_puzzle_solver/output/logic_puzzle_2026-07-21_00-01-54.md (20.6s, attempts=3)
INFO:spl.executor:RETURN: 2749 chars | status=complete, arm=solver, roundtrip=match

Status:  complete
Output:  # Logic Puzzle Report

**Puzzle:** There are 3 houses in a row, numbered 1 to 3 from left to right. Each house has a unique color (Red, Green, Blue), is occupied by a person of a unique nationality (Brit, Swede, Dane), and that person drinks a unique beverage (Tea, Coffee, Milk). Clues: (1) The Brit lives in the Red house. (2) The Swede drinks Tea. (3) The Dane lives in house 1. (4) The owner of the Green house drinks Coffee. (5) The Blue house is house 2. Who drinks Coffee?

**CSP solver status:** `Unique`
**Solutions found:** `1`
**Ground-truth answer:** `Dane`
**Round-trip check:** `match`

## Interpretation

The puzzle asks who drinks Coffee among three house-owners.

The solver found a unique solution: the **Dane** drinks Coffee. House 1 is Green, occupied by the Dane, who drinks Coffee — clue (3) places the Dane in house 1, and clue (4) ties the Green house to Coffee, locking in the answer.

Final answer: Dane

## Solver Code (LLM-generated, python-constraint)

```python
p = Problem()
colors = ['Red', 'Green', 'Blue']
nations = ['Brit', 'Swede', 'Dane']
beverages = ['Tea', 'Coffee', 'Milk']

for c in colors:
    p.addVariable(f'color_{c}', [1, 2, 3])
for n in nations:
    p.addVariable(f'nation_{n}', [1, 2, 3])
for b in beverages:
    p.addVariable(f'bev_{b}', [1, 2, 3])

p.addConstraint(AllDifferentConstraint(), [f'color_{c}' for c in colors])
p.addConstraint(AllDifferentConstraint(), [f'nation_{n}' for n in nations])
p.addConstraint(AllDifferentConstraint(), [f'bev_{b}' for b in beverages])

# Clue 1: Brit lives in the Red house
p.addConstraint(lambda a, b: a == b, ['nation_Brit', 'color_Red'])
# Clue 2: Swede drinks Tea
p.addConstraint(lambda a, b: a == b, ['nation_Swede', 'bev_Tea'])
# Clue 3: Dane lives in house 1
p.addConstraint(lambda a: a == 1, ['nation_Dane'])
# Clue 4: Green house owner drinks Coffee
p.addConstraint(lambda a, b: a == b, ['color_Green', 'bev_Coffee'])
# Clue 5: Blue house is house 2
p.addConstraint(lambda a: a == 2, ['color_Blue'])

solutions = p.getSolutions()
if len(solutions) == 1:
    sol = solutions[0]
    house_of = {}
    for h in [1, 2, 3]:
        color = [c for c in colors if sol[f'color_{c}'] == h][0]
        nation = [n for n in nations if sol[f'nation_{n}'] == h][0]
        bev = [b for b in beverages if sol[f'bev_{b}'] == h][0]
        house_of[h] = {"color": color, "nationality": nation, "beverage": bev}
    coffee_house = sol['bev_Coffee']
    coffee_drinker = house_of[coffee_house]['nationality']
    _result = {"status": "Unique", "n_solutions": 1, "answer": coffee_drinker, "houses": house_of}
elif len(solutions) == 0:
    _result = {"status": "NoSolution", "n_solutions": 0}
else:
    _result = {"status": "Ambiguous", "n_solutions": len(solutions)}
```
LLM calls: 2  Latency: 20596ms
Log:     /home/gongai/.spl/logs/logic_puzzle_solver-claude_cli-claude-sonnet-4-6-20260721-000154.md
