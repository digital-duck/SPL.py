"""Recipe 106 — Shapely Geospatial Coverage Analyzer.

Given delivery zones as polygons and a city boundary, computes:
  - Zone overlaps (routing conflicts)
  - Coverage gaps (unserved areas)
  - Point-in-zone assignment for customer locations
  - Total coverage ratio

Uses Shapely for all geometric operations (no PostGIS/database required).
"""

import json


# ── Default delivery zone problem ────────────────────────────────────────────

_DEFAULT_ZONES = {
    "city_name": "Maplewood",
    "city_boundary": [
        [0, 0], [10, 0], [10, 8], [0, 8], [0, 0]
    ],
    "zones": [
        {
            "name": "Zone A (North)",
            "color": "blue",
            "polygon": [[0, 4], [6, 4], [6, 8], [0, 8], [0, 4]],
            "driver": "Alice",
        },
        {
            "name": "Zone B (South-West)",
            "color": "green",
            "polygon": [[0, 0], [7, 0], [7, 5], [0, 5], [0, 0]],
            "driver": "Bob",
        },
        {
            "name": "Zone C (East)",
            "color": "red",
            "polygon": [[6, 0], [10, 0], [10, 6], [6, 6], [6, 0]],
            "driver": "Carol",
        },
    ],
    "customers": [
        {"id": "C001", "name": "Main St Bakery",  "x": 3,  "y": 6},
        {"id": "C002", "name": "Elm Ave Market",  "x": 3,  "y": 2},
        {"id": "C003", "name": "Oak Park Cafe",   "x": 8,  "y": 3},
        {"id": "C004", "name": "River View Deli", "x": 9,  "y": 7},
        {"id": "C005", "name": "NE Corner Shop",  "x": 8,  "y": 7},
    ],
}


def get_default_zones() -> str:
    """Return default delivery zone problem JSON."""
    return json.dumps(_DEFAULT_ZONES)


def analyze_coverage(zones_json: str) -> str:
    """Compute coverage analysis using Shapely.

    Returns:
      {"city_name": str, "city_area": float, "total_covered_area": float,
       "coverage_ratio": float, "overlaps": [...], "gaps": [...],
       "assignments": [{customer_id, zone_name}], "status": "OK"}
    """
    try:
        from shapely.geometry import Polygon, Point
        from shapely.ops import unary_union
    except ImportError:
        return json.dumps({"status": "ERROR",
                           "error": "shapely not installed — run: pip install shapely"})

    try:
        data  = json.loads(zones_json)
        city  = Polygon(data["city_boundary"])
        zones = {z["name"]: Polygon(z["polygon"]) for z in data["zones"]}
        zone_list = list(zones.items())

        # Pairwise overlaps
        overlaps = []
        for i in range(len(zone_list)):
            for j in range(i + 1, len(zone_list)):
                n1, p1 = zone_list[i]
                n2, p2 = zone_list[j]
                inter  = p1.intersection(p2)
                if not inter.is_empty and inter.area > 1e-9:
                    overlaps.append({
                        "zone_a": n1,
                        "zone_b": n2,
                        "overlap_area": round(inter.area, 4),
                        "overlap_pct_a": round(inter.area / p1.area * 100, 1),
                        "conflict": "routing conflict — two drivers serve same area",
                    })

        # Coverage gaps (city area not covered by any zone)
        covered = unary_union(list(zones.values())).intersection(city)
        gap     = city.difference(covered)
        gaps    = []
        if not gap.is_empty and gap.area > 1e-9:
            gaps.append({
                "area": round(gap.area, 4),
                "pct_city": round(gap.area / city.area * 100, 1),
                "description": "Area within city boundary with no delivery zone assigned",
            })

        # Point-in-zone customer assignment
        assignments = []
        for cust in data.get("customers", []):
            pt       = Point(cust["x"], cust["y"])
            assigned = []
            for name, poly in zones.items():
                if poly.contains(pt) or poly.touches(pt):
                    assigned.append(name)
            assignments.append({
                "customer_id": cust["id"],
                "customer_name": cust.get("name", cust["id"]),
                "x": cust["x"],
                "y": cust["y"],
                "zones": assigned,
                "in_city": city.contains(pt),
                "conflict": len(assigned) > 1,
                "unassigned": len(assigned) == 0,
            })

        coverage_ratio = round(covered.area / city.area, 4) if city.area > 0 else 0.0

        return json.dumps({
            "city_name":         data.get("city_name", "City"),
            "city_area":         round(city.area, 4),
            "total_covered_area": round(covered.area, 4),
            "coverage_ratio":    coverage_ratio,
            "n_overlaps":        len(overlaps),
            "n_gaps":            len(gaps),
            "overlaps":          overlaps,
            "gaps":              gaps,
            "assignments":       assignments,
            "status":            "OK",
        })

    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})


def coverage_is_valid(result_json: str) -> bool:
    """ASSERT gate: analysis ran successfully."""
    try:
        return json.loads(result_json).get("status") == "OK"
    except Exception:
        return False


def format_coverage_report(result_json: str) -> str:
    """Markdown report of coverage analysis."""
    try:
        data  = json.loads(result_json)
        lines = [
            f"## Geospatial Coverage Report — {data.get('city_name', 'City')}",
            "",
            f"**City area:** {data.get('city_area', '?')} km²  ",
            f"**Covered area:** {data.get('total_covered_area', '?')} km²  ",
            f"**Coverage ratio:** {data.get('coverage_ratio', 0):.1%}  ",
            f"**Routing conflicts:** {data.get('n_overlaps', 0)}  ",
            f"**Coverage gaps:** {data.get('n_gaps', 0)}",
            "",
        ]

        if data.get("overlaps"):
            lines += ["### Routing Conflicts (zone overlaps)", "",
                      "| Zone A | Zone B | Overlap Area | % of Zone A |",
                      "|---|---|---|---|"]
            for ov in data["overlaps"]:
                lines.append(
                    f"| {ov['zone_a']} | {ov['zone_b']} "
                    f"| {ov['overlap_area']} km² | {ov['overlap_pct_a']}% |"
                )
            lines.append("")

        if data.get("gaps"):
            lines += ["### Coverage Gaps", ""]
            for g in data["gaps"]:
                lines.append(f"- **{g['area']} km² uncovered** ({g['pct_city']}% of city)")
            lines.append("")

        if data.get("assignments"):
            lines += ["### Customer Zone Assignments", "",
                      "| Customer | Location | Assigned Zone(s) | Conflict |",
                      "|---|---|---|---|"]
            for a in data["assignments"]:
                zone_str = ", ".join(a["zones"]) if a["zones"] else "UNASSIGNED"
                conflict = "⚠ overlap" if a["conflict"] else ("✗ unserved" if a["unassigned"] else "✓")
                lines.append(
                    f"| {a['customer_name']} | ({a['x']}, {a['y']}) "
                    f"| {zone_str} | {conflict} |"
                )

        return "\n".join(lines)
    except Exception as e:
        return f"(format error: {e})"


def json_get_field(data_json: str, field: str) -> str:
    try:
        v = json.loads(data_json).get(field)
        return str(v) if v is not None else ""
    except Exception:
        return ""
