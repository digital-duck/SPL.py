# SPL Run: platypus_moea

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 2267 in / 529 out
- **Latency:** 49001ms
- **Timestamp:** 2026-09-07 08:58:46

## Output

```output
=== Platypus MOEA Workforce Scheduling (r121) | solver=ON ===

Problem:
A service center runs 3 shift types. Day shift: $100/employee, 0.90 service quality, 0.10 fatigue risk, min 10 max 20 staff. Evening shift: $130/employee, 1.00 quality, 0.25 risk, min 10 max 20. Night shift: $160/employee, 0.70 quality, 0.40 risk, min 10 max 20. Total minimum: 30 staff. Find staffing plans that minimize cost, maximize quality, and minimize fatigue risk simultaneously.

Utopia Anchors (per-objective best):
{"min_cost": {"cost": 3900.0, "quality": 0.866667, "risk": 0.25, "xD": 10.0, "xE": 10.0, "xN": 10.0}, "max_quality": {"cost": 7800.0, "quality": 0.866667, "risk": 0.25, "xD": 20.0, "xE": 20.0, "xN": 20.0}, "min_risk": {"cost": 3900.0, "quality": 0.866667, "risk": 0.25, "xD": 10.0, "xE": 10.0, "xN": 10.0}}

Pareto Surface (100 non-dominated points):
| xD | xE | xN | Cost ($) | Quality | Risk | Algorithm |
|---|---|---|---|---|---|---|
| 10 | 10 | 10 | 3,900 | 0.8667 | 0.2500 | platypus-NSGA-II |
| 11 | 10 | 10 | 4,000 | 0.8677 | 0.2452 | platypus-NSGA-II |
| 10 | 11 | 10 | 4,030 | 0.8710 | 0.2500 | platypus-NSGA-II |
| 12 | 10 | 10 | 4,100 | 0.8688 | 0.2406 | platypus-NSGA-II |
| 11 | 11 | 10 | 4,130 | 0.8719 | 0.2453 | platypus-NSGA-II |
| 13 | 10 | 10 | 4,200 | 0.8697 | 0.2364 | platypus-NSGA-II |
| 12 | 11 | 10 | 4,230 | 0.8727 | 0.2409 | platypus-NSGA-II |
| 11 | 12 | 10 | 4,260 | 0.8758 | 0.2455 | platypus-NSGA-II |
| 10 | 13 | 10 | 4,290 | 0.8788 | 0.2500 | platypus-NSGA-II |
| 14 | 10 | 10 | 4,300 | 0.8706 | 0.2324 | platypus-NSGA-II |
| 13 | 11 | 10 | 4,330 | 0.8735 | 0.2368 | platypus-NSGA-II |
| 12 | 12 | 10 | 4,360 | 0.8765 | 0.2412 | platypus-NSGA-II |
| 11 | 13 | 10 | 4,390 | 0.8794 | 0.2456 | platypus-NSGA-II |
| 15 | 10 | 10 | 4,400 | 0.8714 | 0.2286 | platypus-NSGA-II |
| 14 | 11 | 10 | 4,430 | 0.8743 | 0.2329 | platypus-NSGA-II |
| 13 | 12 | 10 | 4,460 | 0.8771 | 0.2371 | platypus-NSGA-II |
| 12 | 13 | 10 | 4,490 | 0.8800 | 0.2414 | platypus-NSGA-II |
| 16 | 10 | 10 | 4,500 | 0.8722 | 0.2250 | platypus-NSGA-II |
| 15 | 11 | 10 | 4,530 | 0.8750 | 0.2292 | platypus-NSGA-II |
| 14 | 12 | 10 | 4,560 | 0.8778 | 0.2333 | platypus-NSGA-II |
| 13 | 13 | 10 | 4,590 | 0.8806 | 0.2375 | platypus-NSGA-II |
| 17 | 10 | 10 | 4,600 | 0.8730 | 0.2216 | platypus-NSGA-II |
| 12 | 14 | 10 | 4,620 | 0.8833 | 0.2417 | platypus-NSGA-II |
| 16 | 11 | 10 | 4,630 | 0.8757 | 0.2257 | platypus-NSGA-II |
| 15 | 12 | 10 | 4,660 | 0.8784 | 0.2297 | platypus-NSGA-II |
| 14 | 13 | 10 | 4,690 | 0.8811 | 0.2338 | platypus-NSGA-II |
| 18 | 10 | 10 | 4,700 | 0.8737 | 0.2184 | platypus-NSGA-II |
| 13 | 14 | 10 | 4,720 | 0.8838 | 0.2378 | platypus-NSGA-II |
| 17 | 11 | 10 | 4,730 | 0.8763 | 0.2224 | platypus-NSGA-II |
| 12 | 15 | 10 | 4,750 | 0.8865 | 0.2419 | platypus-NSGA-II |
| 16 | 12 | 10 | 4,760 | 0.8789 | 0.2263 | platypus-NSGA-II |
| 11 | 16 | 10 | 4,780 | 0.8892 | 0.2459 | platypus-NSGA-II |
| 15 | 13 | 10 | 4,790 | 0.8816 | 0.2303 | platypus-NSGA-II |
| 19 | 10 | 10 | 4,800 | 0.8744 | 0.2154 | platypus-NSGA-II |
| 10 | 17 | 10 | 4,810 | 0.8919 | 0.2500 | platypus-NSGA-II |
| 14 | 14 | 10 | 4,820 | 0.8842 | 0.2342 | platypus-NSGA-II |
| 18 | 11 | 10 | 4,830 | 0.8769 | 0.2192 | platypus-NSGA-II |
| 13 | 15 | 10 | 4,850 | 0.8868 | 0.2382 | platypus-NSGA-II |
| 17 | 12 | 10 | 4,860 | 0.8795 | 0.2231 | platypus-NSGA-II |
| 12 | 16 | 10 | 4,880 | 0.8895 | 0.2421 | platypus-NSGA-II |
| 16 | 13 | 10 | 4,890 | 0.8821 | 0.2269 | platypus-NSGA-II |
| 20 | 10 | 10 | 4,900 | 0.8750 | 0.2125 | platypus-NSGA-II |
| 15 | 14 | 10 | 4,920 | 0.8846 | 0.2308 | platypus-NSGA-II |
| 19 | 11 | 10 | 4,930 | 0.8775 | 0.2162 | platypus-NSGA-II |
| 10 | 18 | 10 | 4,940 | 0.8947 | 0.2500 | platypus-NSGA-II |
| 14 | 15 | 10 | 4,950 | 0.8872 | 0.2346 | platypus-NSGA-II |
| 18 | 12 | 10 | 4,960 | 0.8800 | 0.2200 | platypus-NSGA-II |
| 13 | 16 | 10 | 4,980 | 0.8897 | 0.2385 | platypus-NSGA-II |
| 17 | 13 | 10 | 4,990 | 0.8825 | 0.2238 | platypus-NSGA-II |
| 16 | 14 | 10 | 5,020 | 0.8850 | 0.2275 | platypus-NSGA-II |
| 20 | 11 | 10 | 5,030 | 0.8780 | 0.2134 | platypus-NSGA-II |
| 15 | 15 | 10 | 5,050 | 0.8875 | 0.2313 | platypus-NSGA-II |
| 19 | 12 | 10 | 5,060 | 0.8805 | 0.2171 | platypus-NSGA-II |
| 10 | 19 | 10 | 5,070 | 0.8974 | 0.2500 | platypus-NSGA-II |
| 14 | 16 | 10 | 5,080 | 0.8900 | 0.2350 | platypus-NSGA-II |
| 18 | 13 | 10 | 5,090 | 0.8829 | 0.2207 | platypus-NSGA-II |
| 13 | 17 | 10 | 5,110 | 0.8925 | 0.2387 | platypus-NSGA-II |
| 17 | 14 | 10 | 5,120 | 0.8854 | 0.2244 | platypus-NSGA-II |
| 12 | 18 | 10 | 5,140 | 0.8950 | 0.2425 | platypus-NSGA-II |
| 16 | 15 | 10 | 5,150 | 0.8878 | 0.2280 | platypus-NSGA-II |
| 20 | 12 | 10 | 5,160 | 0.8810 | 0.2143 | platypus-NSGA-II |
| 15 | 16 | 10 | 5,180 | 0.8902 | 0.2317 | platypus-NSGA-II |
| 19 | 13 | 10 | 5,190 | 0.8833 | 0.2179 | platypus-NSGA-II |
| 14 | 17 | 10 | 5,210 | 0.8927 | 0.2354 | platypus-NSGA-II |
| 18 | 14 | 10 | 5,220 | 0.8857 | 0.2214 | platypus-NSGA-II |
| 17 | 15 | 10 | 5,250 | 0.8881 | 0.2250 | platypus-NSGA-II |
| 16 | 16 | 10 | 5,280 | 0.8905 | 0.2286 | platypus-NSGA-II |
| 20 | 13 | 10 | 5,290 | 0.8837 | 0.2151 | platypus-NSGA-II |
| 11 | 20 | 10 | 5,300 | 0.9000 | 0.2463 | platypus-NSGA-II |
| 15 | 17 | 10 | 5,310 | 0.8929 | 0.2321 | platypus-NSGA-II |
| 19 | 14 | 10 | 5,320 | 0.8860 | 0.2186 | platypus-NSGA-II |
| 14 | 18 | 10 | 5,340 | 0.8952 | 0.2357 | platypus-NSGA-II |
| 18 | 15 | 10 | 5,350 | 0.8884 | 0.2221 | platypus-NSGA-II |
| 13 | 19 | 10 | 5,370 | 0.8976 | 0.2393 | platypus-NSGA-II |
| 17 | 16 | 10 | 5,380 | 0.8907 | 0.2256 | platypus-NSGA-II |
| 12 | 20 | 10 | 5,400 | 0.9000 | 0.2429 | platypus-NSGA-II |
| 20 | 14 | 10 | 5,420 | 0.8864 | 0.2159 | platypus-NSGA-II |
| 14 | 19 | 10 | 5,470 | 0.8977 | 0.2360 | platypus-NSGA-II |
| 18 | 16 | 10 | 5,480 | 0.8909 | 0.2227 | platypus-NSGA-II |
| 13 | 20 | 10 | 5,500 | 0.9000 | 0.2395 | platypus-NSGA-II |
| 17 | 17 | 10 | 5,510 | 0.8932 | 0.2261 | platypus-NSGA-II |
| 16 | 18 | 10 | 5,540 | 0.8955 | 0.2295 | platypus-NSGA-II |
| 20 | 15 | 10 | 5,550 | 0.8889 | 0.2167 | platypus-NSGA-II |
| 18 | 17 | 10 | 5,610 | 0.8933 | 0.2233 | platypus-NSGA-II |
| 17 | 18 | 10 | 5,640 | 0.8956 | 0.2267 | platypus-NSGA-II |
| 16 | 19 | 10 | 5,670 | 0.8978 | 0.2300 | platypus-NSGA-II |
| 20 | 16 | 10 | 5,680 | 0.8913 | 0.2174 | platypus-NSGA-II |
| 19 | 17 | 10 | 5,710 | 0.8935 | 0.2207 | platypus-NSGA-II |
| 18 | 18 | 10 | 5,740 | 0.8957 | 0.2239 | platypus-NSGA-II |
| 17 | 19 | 10 | 5,770 | 0.8978 | 0.2272 | platypus-NSGA-II |
| 20 | 17 | 10 | 5,810 | 0.8936 | 0.2181 | platypus-NSGA-II |
| 19 | 18 | 10 | 5,840 | 0.8957 | 0.2213 | platypus-NSGA-II |
| 18 | 19 | 10 | 5,870 | 0.8979 | 0.2245 | platypus-NSGA-II |
| 17 | 20 | 10 | 5,900 | 0.9000 | 0.2277 | platypus-NSGA-II |
| 20 | 18 | 10 | 5,940 | 0.8958 | 0.2188 | platypus-NSGA-II |
| 19 | 19 | 10 | 5,970 | 0.8979 | 0.2219 | platypus-NSGA-II |
| 18 | 20 | 10 | 6,000 | 0.9000 | 0.2250 | platypus-NSGA-II |
| 20 | 19 | 10 | 6,070 | 0.8980 | 0.2194 | platypus-NSGA-II |
| 19 | 20 | 10 | 6,100 | 0.9000 | 0.2224 | platypus-NSGA-II |
| 20 | 20 | 10 | 6,200 | 0.9000 | 0.2200 | platypus-NSGA-II |

**Cost:** $3,900 – $6,200  |  **Quality:** 0.8667 – 0.9000  |  **Risk:** 0.2125 – 0.2500

Interpretation:
## Pareto Surface Interpretation: 3-Shift Workforce Planning

### 1. The 3-Way Tradeoff

Night shifts dominate all three objectives negatively — costliest ($160), lowest quality (0.70), highest fatigue risk (0.40) — so the solver locks them at the minimum (10) across every solution. The real tension is **Day vs. Evening**: adding Day staff ($100, risk 0.10) simultaneously lowers cost *and* risk, while adding Evening staff ($130, quality 1.00) raises quality but at higher cost and moderate risk. Cost and risk are therefore **aligned allies**; quality is the competing objective.

### 2. Recommended Operating Points

| Scenario | Plan (D/E/N) | Cost | Quality | Risk | When to use |
|---|---|---|---|---|---|
| Budget-constrained | 10 / 10 / 10 | $3,900 | 0.867 | 0.250 | Off-peak or overnight low-demand periods |
| Quality-maximizing | 20 / 20 / 10 | $6,200 | 0.900 | 0.220 | Customer-facing peaks (holidays, launches) |
| Balanced | 15 / 13 / 10 | $4,790 | 0.882 | 0.230 | Typical weekday operations |

The **balanced point** spends 23% more than minimum for a meaningful quality gain (+1.7%) and a meaningful risk reduction (-8.4%) — the steepest part of the efficiency curve.

### 3. Distance from Utopia

The Pareto front **fully achieves** two of three utopia anchors: minimum cost ($3,900) and maximum achievable quality (0.900, constrained by the night-shift floor). The minimum-risk anchor stated in the problem data appears miscalculated (it lists (10,10,10) with risk 0.25, but the Pareto front actually reaches 0.2125 at (20,10,10)). In practice, the solver found the true risk minimum.

### 4. Practical Recommendation

For a typical service center, staff **15 Day / 13 Evening / 10 Night** — this balanced plan captures most of the quality and safety gains at roughly half the incremental budget between minimum and maximum staffing.

LLM calls: 2
```
