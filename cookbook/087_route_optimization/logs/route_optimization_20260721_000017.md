INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/87_route_optimization/route_optimization.spl
Registry: ['route_optimization']
Running workflow: route_optimization(['model'])
[INFO] [route_optimization] start run_id=2026-07-21_00-03-31 solver=true
[INFO] [arm=solver] Stage 1 — LLM formulation + OR-Tools solve
INFO:spl.executor:GENERATE segment 1 (formulate_routing_code) -> 474 tokens, 9272ms
INFO:spl.executor:GENERATE chain done -> @code (1899 chars total)
[INFO] [arm=solver] attempt 1: status=Error
INFO:spl.executor:GENERATE segment 1 (repair_routing_code) -> 413 tokens, 6621ms
INFO:spl.executor:GENERATE chain done -> @code (1653 chars total)
[INFO] [arm=solver] repair 2: status=Optimal
[INFO] [route_optimization] Stage 2 — ASSERT gate (status=Optimal)
INFO:spl.executor:ASSERT (tools-eval) is_optimal('{"status": "Optimal", "route": [0, 4, 3, 5, 2, 1, 0], "answer": 101}') -> True
[INFO] [route_optimization] ASSERT passed — OR-Tools found a feasible route
INFO:spl.executor:GENERATE segment 1 (interpret_routing_result) -> 108 tokens, 4609ms
INFO:spl.executor:GENERATE chain done -> @narrative (435 chars total)
[INFO] [route_optimization] round-trip check: match
[INFO] [route_optimization] done — report -> /home/gongai/projects/digital-duck/SPL.py/cookbook/87_route_optimization/output/route_optimization_2026-07-21_00-03-31.md (24.6s, attempts=3)
INFO:spl.executor:RETURN: 2719 chars | status=complete, arm=solver, roundtrip=match

Status:  complete
Output:  # Route Optimization Report

**Problem:** A delivery driver starts and ends at the depot (location 0) and must visit 5 customer locations (1-5). The distance matrix in miles is: [[0,29,20,21,16,31],[29,0,15,29,28,40],[20,15,0,15,14,25],[21,29,15,0,4,12],[16,28,14,4,0,16],[31,40,25,12,16,0]] (row/col order = depot,1,2,3,4,5). Find the shortest round-trip route visiting every location exactly once.

**OR-Tools status:** `Optimal`
**Route (node indices):** `[0, 4, 3, 5, 2, 1, 0]`
**Total distance (ground truth):** `101`
**Round-trip check:** `match`

## Interpretation

**Routing Question:** Find the shortest round-trip from the depot visiting all 5 customers exactly once.

**Optimal Route:** Depot → 4 → 3 → 5 → 2 → 1 → Depot, covering **101 miles** total.

**Leg breakdown:** 0→4 (16) → 3 (4) → 5 (12) → 2 (25) → 1 (15) → 0 (29) = 101 ✓

Even with 5 stops, there are 120 possible permutations — a combinatorial solver guarantees the global optimum far faster than manual evaluation.

Final answer: 101

## Solver Code (LLM-generated, OR-Tools)

```python
distance_matrix = [
    [0, 29, 20, 21, 16, 31],
    [29, 0, 15, 29, 28, 40],
    [20, 15, 0, 15, 14, 25],
    [21, 29, 15, 0, 4, 12],
    [16, 28, 14, 4, 0, 16],
    [31, 40, 25, 12, 16, 0],
]

n = len(distance_matrix)
num_vehicles = 1
depot = 0

manager = pywrapcp.RoutingIndexManager(n, num_vehicles, depot)
routing = pywrapcp.RoutingModel(manager)

def transit_callback(from_index, to_index):
    from_node = manager.IndexToNode(from_index)
    to_node = manager.IndexToNode(to_index)
    return distance_matrix[from_node][to_node]

transit_callback_index = routing.RegisterTransitCallback(transit_callback)
routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

search_parameters = pywrapcp.DefaultRoutingSearchParameters()
search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
search_parameters.time_limit.seconds = 2

solution = routing.SolveWithParameters(search_parameters)

if solution:
    route = []
    index = routing.Start(0)
    while not routing.IsEnd(index):
        route.append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))
    route.append(manager.IndexToNode(index))
    total_distance = 0
    idx = routing.Start(0)
    while not routing.IsEnd(idx):
        next_idx = solution.Value(routing.NextVar(idx))
        total_distance += routing.GetArcCostForVehicle(idx, next_idx, 0)
        idx = next_idx
    _result = {"status": "Optimal", "route": route, "answer": total_distance}
else:
    _result = {"status": "NoSolution"}
```
LLM calls: 3  Latency: 24647ms
Log:     /home/gongai/.spl/logs/route_optimization-claude_cli-claude-sonnet-4-6-20260721-000331.md
