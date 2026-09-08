# SPL Run: shapely_geo

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 425 in / 254 out
- **Latency:** 12860ms
- **Timestamp:** 2026-09-06 21:57:59

## Output

```output
=== Shapely Coverage Analyzer (r106) | solver=ON ===

## Geospatial Coverage Report — Maplewood

**City area:** 80.0 km²  
**Covered area:** 72.0 km²  
**Coverage ratio:** 90.0%  
**Routing conflicts:** 2  
**Coverage gaps:** 1

### Routing Conflicts (zone overlaps)

| Zone A | Zone B | Overlap Area | % of Zone A |
|---|---|---|---|
| Zone A (North) | Zone B (South-West) | 6.0 km² | 25.0% |
| Zone B (South-West) | Zone C (East) | 5.0 km² | 14.3% |

### Coverage Gaps

- **8.0 km² uncovered** (10.0% of city)

### Customer Zone Assignments

| Customer | Location | Assigned Zone(s) | Conflict |
|---|---|---|---|
| Main St Bakery | (3, 6) | Zone A (North) | ✓ |
| Elm Ave Market | (3, 2) | Zone B (South-West) | ✓ |
| Oak Park Cafe | (8, 3) | Zone C (East) | ✓ |
| River View Deli | (9, 7) | UNASSIGNED | ✗ unserved |
| NE Corner Shop | (8, 7) | UNASSIGNED | ✗ unserved |

── Logistics Explanation ───────────────────────────────────
**1. Zone A/B overlap significance:**
The 6 km² overlap (25% of Zone A) is operationally costly — both Alice and Bob receive dispatch orders for the same addresses, causing duplicate deliveries, driver confusion, and wasted fuel. At scale this erodes margin.

**2. Coverage gap location and affected customers:**
The 8 km² gap sits in the **northeast corner** (roughly x>7, y>6). River View Deli (9,7) and NE Corner Shop (8,7) fall squarely in it — both are unserved with no assigned driver.

**3. Simplest fix:**
Extend Zone C (Carol) northward to cover the northeast quadrant, and redraw the Zone A/B boundary as a clean horizontal line around y=4. This eliminates the A/B overlap and fills the NE gap in one adjustment.

**4. LLM estimation failure:**
An LLM would likely guess a small gap ("maybe 1–2 km²") based on the description "most of the city covered." Exact Shapely geometry reveals the gap is 8 km² — 4× larger — because polygon union calculations require precise vertex coordinates, not prose inference.
```
