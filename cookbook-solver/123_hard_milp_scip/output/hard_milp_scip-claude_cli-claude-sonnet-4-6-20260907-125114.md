# SPL Run: hard_milp_scip

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 313 in / 1582 out
- **Latency:** 81748ms
- **Timestamp:** 2026-09-07 12:51:14

## Output

```output
=== Hard MILP Unit Commitment (r123) | solver=OFF ===

── LLM Merit-Order Heuristic ──────────────────────────────
## Manual Unit Commitment: 5-Generator, 24-Hour Schedule

**Assumed generator parameters** (since none were given — adjust if you have a specific dataset):

| Gen | Type | Pmin | Pmax | MC ($/MWh) | Startup ($) | Min Up | Min Down | Ramp (MW/h) |
|-----|------|------|------|------------|-------------|--------|----------|-------------|
| G1 | Nuclear | 200 | 400 | $12 | $15,000 | 12 h | 12 h | 30 |
| G2 | Coal | 80 | 300 | $22 | $3,000 | 4 h | 4 h | 60 |
| G3 | Gas CC | 40 | 200 | $38 | $1,500 | 2 h | 2 h | 100 |
| G4 | Gas CT | 10 | 150 | $60 | $800 | 1 h | 1 h | 150 |
| G5 | Peaker | 5 | 75 | $90 | $300 | 1 h | 1 h | 75 |

**Demand profile** (simplified 4-block):

| Block | Hours | Load |
|-------|-------|------|
| Midnight | H1–H6 | 500 MW |
| Morning | H7–H12 | 800 MW |
| Afternoon | H13–H18 | 900 MW |
| Evening | H19–H24 | 650 MW |

---

## Question 1: Commitment Schedule by Block

**Rule:** commit generators cheapest-first (G1 → G5) until load is met.

### Block 1 — Midnight (H1–H6, 500 MW)

| Gen | Status | Output |
|-----|--------|--------|
| G1 | **ON** | 400 MW (max) |
| G2 | **ON** | 100 MW |
| G3 | OFF | 0 MW |
| G4 | OFF | 0 MW |
| G5 | OFF | 0 MW |
| **Total** | | **500 MW** |

G1 must stay on all day — 12-hour minimum up time makes it uneconomical to cycle.
G2 must also stay on through morning block to satisfy its 4-hour minimum up time.

---

### Block 2 — Morning (H7–H12, 800 MW)

| Gen | Status | Output |
|-----|--------|--------|
| G1 | **ON** | 400 MW |
| G2 | **ON** | 300 MW (max) |
| G3 | **ON** ← startup | 100 MW |
| G4 | OFF | 0 MW |
| G5 | OFF | 0 MW |
| **Total** | | **800 MW** |

G3 starts cold at H7. Ramp constraint: G3 can reach 100 MW within 1 hour from its 40 MW Pmin ✓.

---

### Block 3 — Afternoon (H13–H18, 900 MW)

| Gen | Status | Output |
|-----|--------|--------|
| G1 | **ON** | 400 MW |
| G2 | **ON** | 300 MW (max) |
| G3 | **ON** | 200 MW (max) |
| G4 | OFF | 0 MW |
| G5 | OFF | 0 MW |
| **Total** | | **900 MW** |

G3 was already on from H7, so no second startup cost.

---

### Block 4 — Evening (H19–H24, 650 MW)

| Gen | Status | Output |
|-----|--------|--------|
| G1 | **ON** | 400 MW |
| G2 | **ON** | 250 MW |
| G3 | OFF ← shutdown at H19 | 0 MW |
| G4 | OFF | 0 MW |
| G5 | OFF | 0 MW |
| **Total** | | **650 MW** |

G3 shuts down at H19 (it had 12 hours on; 2-hour minimum up satisfied). G2 ramps down 50 MW from H18→H19 — within its 60 MW/h ramp limit ✓.

---

## Question 2: Total Generation Cost Estimate

### Energy costs (variable)

| Block | Duration | G1 (400 MW × $12) | G2 | G3 | Hourly total | Block total |
|-------|----------|-------------------|----|----|-------------|-------------|
| Midnight | 6 h | $4,800 | 100×$22=$2,200 | — | $7,000 | **$42,000** |
| Morning | 6 h | $4,800 | 300×$22=$6,600 | 100×$38=$3,800 | $15,200 | **$91,200** |
| Afternoon | 6 h | $4,800 | 300×$22=$6,600 | 200×$38=$7,600 | $19,000 | **$114,000** |
| Evening | 6 h | $4,800 | 250×$22=$5,500 | — | $10,300 | **$61,800** |

**Energy subtotal: $309,000**

### Startup costs (one-time, on first commitment)

| Event | Cost |
|-------|------|
| G1 cold start (H1) | $15,000 |
| G2 cold start (H1) | $3,000 |
| G3 cold start (H7) | $1,500 |

**Startup subtotal: $19,500**

### Grand total: ~$328,500

---

## Question 3: Why This Problem Is Hard

**Startup costs** — each time a generator switches ON, you pay a lump-sum penalty regardless of how long it runs. A greedy hourly decision that avoids a startup in one hour may force two startups later. The decision at H6 about whether to keep G3 on affects H7–H18 costs non-locally.

**Minimum up/down times** — G1's 12-hour minimum up time means you must commit it for at least half the day or not at all. If you start it at H13 to cover the afternoon peak, you're locked in until H1 the next day. This creates look-ahead coupling: the optimal H1 decision depends on what you need at H20.

**Ramp rate limits** — G2 can only change output 60 MW/hour. If load spikes 200 MW in two hours (e.g., cold morning), you need G3 already on and warmed up — not starting it at the spike. This means you must commit generators before they're economically needed, paying idle costs as insurance. The transition from midnight block (500 MW) to morning block (800 MW) requires G3 to start at H5 or H6, not H7, to be ramped up in time — a nuance the block-averaging heuristic above ignores.

**Combined effect** — these three constraints interact: a ramp event triggers early commitment, which triggers a startup cost, which locks the unit in for its minimum up time. The coupling spans the full 24-hour horizon.

---

## Question 4: Why the Heuristic Can't Guarantee Optimality

Four reasons, each concrete:

1. **No startup cost lookahead.** I committed G3 at H7 and shut it down at H19. If demand at H20–H24 spiked back to 850 MW, I'd need a second G3 startup ($1,500). A MILP solver would see this and keep G3 on through H24 if the extra runtime cost is less than a second startup — the heuristic can't reason over this tradeoff.

2. **Block averaging masks within-block variation.** Real demand at H15 might be 950 MW — requiring G4 briefly — while H13 is 870 MW. The 6-hour block average of 900 MW suggests G3 is sufficient, but G4 may be needed for individual hours. Ignoring intra-block variation means the heuristic can miss binding constraints.

3. **Ignored feasibility from ramp limits.** Transitioning from 500 MW (midnight) to 800 MW (morning) in one step: G2 must ramp 200 MW (from 100 to 300) and G3 must ramp 100 MW from cold start. G2's ramp rate is 60 MW/h — that transition takes 3+ hours, not 1. A true optimal schedule pre-positions generators earlier; the heuristic doesn't.

4. **No integer optimality certificate.** Even if I solve the LP relaxation (allowing fractional on/off), the LP lower bound on cost might be $310,000 while my heuristic produces $328,500. The gap of $18,500 tells me better integer solutions exist — but without branch-and-cut (what SCIP provides), I can't close it. The heuristic has no proof of optimality, only a feasible schedule.

**Bottom line:** the heuristic gives a feasible, reasonable schedule (~$328,500), but the MILP optimal is likely $20,000–$50,000 cheaper — savings that come from solving the temporal coupling that a greedy block-by-block approach cannot see.

Note: LLM heuristic cannot certify optimality or guarantee ramp/min-uptime constraints.
Run --param use_solver=true for SCIP certified solution.
```
