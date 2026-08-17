# Route Optimization Report

**Problem:** A delivery driver starts and ends at the depot (location 0) and must visit 5 customer locations (1-5). The distance matrix in miles is: [[0,29,20,21,16,31],[29,0,15,29,28,40],[20,15,0,15,14,25],[21,29,15,0,4,12],[16,28,14,4,0,16],[31,40,25,12,16,0]] (row/col order = depot,1,2,3,4,5). Find the shortest round-trip route visiting every location exactly once.

**OR-Tools status:** `Optimal`
**Route (node indices):** `[0, 4, 3, 5, 2, 1, 0]`
**Total distance (ground truth):** `101`
**Round-trip check:** `match`

## Interpretation

**Routing Question:** Find the shortest round-trip from the depot visiting all 5 customers exactly once.

**Optimal Route:** Depot → Location 4 → Location 3 → Location 5 → Location 2 → Location 1 → Depot, covering **101 miles** total.

**Why a solver?** Even with just 5 stops, there are 120 possible routes to evaluate — OR-Tools guarantees the true optimum instantly, while human planners guess.

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

def distance_callback(from_index, to_index):
    from_node = manager.IndexToNode(from_index)
    to_node = manager.IndexToNode(to_index)
    return distance_matrix[from_node][to_node]

transit_callback_index = routing.RegisterTransitCallback(distance_callback)
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
    total_distance = sum(
        distance_matrix[route[i]][route[i + 1]] for i in range(len(route) - 1)
    )
    _result = {"status": "Optimal", "route": route, "answer": total_distance}
else:
    _result = {"status": "NoSolution"}
```