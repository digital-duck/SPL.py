# SPL Run: shapely_geo

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 354 in / 550 out
- **Latency:** 49058ms
- **Timestamp:** 2026-09-06 23:43:39

## Output

```output
=== Shapely Coverage Analyzer (r106) | solver=OFF ===

── LLM Coverage Estimate ───────────────────────────────────
## Delivery Zone Coverage Analysis — Maplewood City

### 1. Zone Overlap: A ∩ B

Zone A occupies **x ∈ [0, 6], y ∈ [4, 8]**.
Zone B occupies **x ∈ [0, 7], y ∈ [0, 5]**.

The overlap is the intersection of both rectangles:
- x: [0, min(6,7)] = **[0, 6]** → width = 6 km
- y: [max(4,0), min(8,5)] = **[4, 5]** → height = 1 km

**A ∩ B ≈ 6 km²** (a horizontal strip across the upper-left, y = 4–5, x = 0–6).

Other overlaps:
- **A ∩ C**: They share only the vertical line x = 6 — zero area overlap.
- **B ∩ C**: x ∈ [6,7], y ∈ [0,5] → 1 × 5 = **5 km²** (a narrow strip on the east edge of Zone B).

---

### 2. Uncovered Area

Using inclusion-exclusion:

| Component | Area |
|-----------|------|
| A + B + C | 24 + 35 + 24 = 83 |
| − A∩B − B∩C | − 6 − 5 = −11 |
| **Union** | **72 km²** |
| City total | 80 km² |
| **Gap** | **8 km²** |

**Where is the gap?** Zone C's northern boundary is y = 6; Zone A's eastern boundary is x = 6. Neither zone (nor Zone B, which stops at y = 5) covers the **northeast rectangle x ∈ [6, 10], y ∈ [6, 8]**.

> The northeast corner — a 4 × 2 km block — is entirely unserved.

---

### 3. Customer Zone Assignments

| Customer | Location | In A? | In B? | In C? | Assignment |
|----------|----------|-------|-------|-------|------------|
| C001 Main St Bakery | (3, 6) | ✓ (x≤6, y≥4) | ✗ (y>5) | ✗ (x<6) | **Zone A — Alice** |
| C002 Elm Ave Market | (3, 2) | ✗ (y<4) | ✓ (x≤7, y≤5) | ✗ (x<6) | **Zone B — Bob** |
| C003 Oak Park Cafe | (8, 3) | ✗ (x>6) | ✗ (x>7) | ✓ (x≥6, y≤6) | **Zone C — Carol** |
| C004 River View Deli | (9, 7) | ✗ (x>6) | ✗ (x>7) | ✗ (y>6) | **UNSERVED** |
| C005 NE Corner Shop | (8, 7) | ✗ (x>6) | ✗ (x>7) | ✗ (y>6) | **UNSERVED** |

---

### 4. Conflict and Unserved Customers

**No customers fall in a conflict (dual-zone) area** — the A∩B strip (y=4–5) and B∩C strip (x=6–7) happen to contain none of the five locations.

**Two customers are unserved:**
- **C004 River View Deli (9, 7)** — northeast gap
- **C005 NE Corner Shop (8, 7)** — northeast gap

**Recommendation:** Extend Zone C's northern boundary from y = 6 to y = 8 (adding 4 × 2 = 8 km² to Carol's territory) to close the gap and serve both unserved customers at no overlap cost.

Note: LLM estimates without exact geometry. Run with --param use_solver=true
to compute exact overlap and gap areas with Shapely.
```
