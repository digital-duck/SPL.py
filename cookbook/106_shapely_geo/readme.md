# Recipe 106 — Shapely Geospatial Coverage Analyzer

**The key story:** Three delivery zones in Maplewood have a 6 km² routing conflict (Zone A ∩ Zone B) and a 5 km² conflict (Zone B ∩ Zone C), plus an 8 km² northeast gap where no driver is assigned (10% of city uncovered). Shapely computes all of this exactly in <0.01s. For axis-aligned rectangles the LLM can also compute correct answers via inclusion-exclusion arithmetic — but it would fail on irregular or rotated polygons where Shapely's comparative advantage is decisive.

## What it demonstrates

| Axis | solver=ON | solver=OFF |
|---|---|---|
| Engine | Shapely polygon geometry | LLM spatial estimation from description |
| Output | Exact overlap/gap areas, point-in-zone assignments | Rough estimate: "Zone A and B probably overlap a bit" |
| Guarantee | Mathematically exact (floating point) | Approximate, misses edge cases |
| Verification | `ASSERT coverage_is_valid` (C1) | — |
| Solver class | C1 (categorical: OK / ERROR) + C3 (independent geometric computation) | — |

## Default problem (Maplewood city, 10×8 km)

```
(0,8)──────────────────(10,8)
  │  Zone A (North)    │ GAP │
  │  [0,4]→[6,8]       │     │
(0,4)────────(6,4)    │     │
  │           │  OVERLAP    │
  │  Zone B   │  Zone A∩B   │ Zone C (East)
  │  (South-W)│  [0,4]→[6,5]│ [6,0]→[10,6]
  │  [0,0]→[7,5]       │     │
(0,0)────────────────(10,0)
```

Zone A: [0,4]→[6,8] = 30 km²  
Zone B: [0,0]→[7,5] = 35 km²  
Zone C: [6,0]→[10,6] = 24 km²  
City: 10×8 = 80 km²

## Key findings (solver=ON)

| Finding | Value |
|---|---|
| Zone A ∩ Zone B overlap | 6 km² — 25% of Zone A (routing conflict: Alice + Bob) |
| Zone B ∩ Zone C overlap | 5 km² — 14.3% of Zone B (routing conflict: Bob + Carol) |
| Northeast gap (x>6, y>6) | 8 km² uncovered — 10% of city |
| Coverage ratio | 90% (72 km² of 80 km²) |
| C004 River View Deli (9,7) | UNASSIGNED — in the gap |
| C005 NE Corner Shop (8,7) | UNASSIGNED — in the gap |

## Run results — solver=ON vs solver=OFF

Both runs used `claude_cli` / `claude-sonnet-4-6` on the same Maplewood dataset (3 zones, 5 customers, 10×8 km city).

| Metric | solver=ON | solver=OFF |
|---|---|---|
| Timestamp | 2026-09-06 21:57:59 | 2026-09-06 23:43:39 |
| Tokens in | 425 | 354 |
| Tokens out | 254 | 550 |
| Total tokens | 679 | 904 (+33%) |
| Latency | 12.9s | 49.1s (3.8×) |
| A∩B overlap | 6.0 km² ✓ | 6.0 km² ✓ |
| B∩C overlap | 5.0 km² ✓ | 5.0 km² ✓ |
| Coverage gap | 8.0 km² ✓ | 8.0 km² ✓ |
| Gap location | NE corner ✓ | NE corner, x∈[6,10] y∈[6,8] ✓ |
| Customer assignments | All 5 correct ✓ | All 5 correct ✓ |
| Customers in conflict zones | 0 (correct) ✓ | 0 (correct) ✓ |

### Key finding: solver=OFF was accurate — on this problem

The LLM applied inclusion-exclusion correctly across all three rectangle pairs and identified the exact 4×2 km northeast gap. All values match Shapely's output to the km². This is an outlier result compared to r103–r105: **simple axis-aligned rectangles are amenable to pencil-and-paper arithmetic**, which LLMs handle well.

### Where solver=OFF would fail

| Polygon type | LLM | Shapely |
|---|---|---|
| Axis-aligned rectangles | ✓ correct (this run) | ✓ exact |
| Rotated rectangles | ✗ likely wrong (sin/cos errors) | ✓ exact |
| Irregular polygons | ✗ wrong | ✓ exact |
| Non-convex shapes | ✗ wrong | ✓ exact |
| Polygon with holes | ✗ wrong | ✓ exact |
| 10+ zone overlap matrix | ✗ combinatorial explosion | ✓ exact |

### Key takeaway

solver=ON is 3.8× faster and uses 25% fewer output tokens. The accuracy gap here is zero because the zones happen to be rectangles — a best-case scenario for LLM spatial reasoning. In production delivery logistics, zones are rarely rectangular: they follow streets, admin boundaries, and terrain. Any deviation from axis-alignment makes LLM spatial arithmetic unreliable. Shapely's value is not that it does better on simple cases — it's that it scales correctly to cases the LLM cannot handle at all.

## Run commands

```bash
# solver=ON — Shapely exact geometry
spl3 run cookbook/106_shapely_geo/shapely_geo.spl \
    --llm claude_cli --param use_solver=true

# solver=OFF — LLM spatial estimate
spl3 run cookbook/106_shapely_geo/shapely_geo.spl \
    --llm claude_cli --param use_solver=false
```

## Install

```bash
conda activate spl123
pip install shapely
```

## TOOL_API reference

| Function | Purpose |
|---|---|
| `get_default_zones()` | Returns Maplewood zone JSON (3 zones, 5 customers) |
| `analyze_coverage(zones_json)` | Shapely: overlaps, gaps, point-in-zone assignments |
| `coverage_is_valid(result_json)` | ASSERT gate: `status == "OK"` |
| `format_coverage_report(result_json)` | Markdown tables: conflicts, gaps, customer assignments |

## Geometry operations used

- `Polygon.intersection(other)` — compute overlap area between two zones
- `unary_union(polygons)` — merge all zones into a single covered region
- `city.difference(covered)` — find the uncovered gap inside city boundary
- `Polygon.contains(Point)` — assign each customer to their zone

## Real-world applications

- **Delivery logistics**: detect routing conflicts between driver territories
- **Telecom coverage**: find dead zones and overlapping cell tower footprints
- **Zoning compliance**: verify that a new development falls within permitted zones
- **Emergency services**: ensure no address is outside every fire station's service radius

## Related recipes

- r102: Z3 SMT — logical constraints over eligibility rules (not geometric)
- r107: workforce optimization — 3-objective Pareto over shift assignments
- r100: supply sourcing — geographic supplier selection (non-spatial but location-aware)
