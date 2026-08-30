## Setting Up the Problem

Let **x** = number of chairs, **y** = number of tables.

**Maximize:** Profit = 20x + 30y

**Subject to:**
- Labor: 2x + 4y ≤ 20
- Wood: 4x + 3y ≤ 24
- x, y ≥ 0

## Finding the Feasible Region's Corners

**Labor constraint** (2x + 4y = 20): intercepts at (10, 0) and (0, 5)
**Wood constraint** (4x + 3y = 24): intercepts at (6, 0) and (0, 8)

The binding vertices of the feasible region are:

| Point | How it arises |
|---|---|
| (0, 0) | Origin |
| (6, 0) | Wood constraint hits x-axis first (6 < 10) |
| (0, 5) | Labor constraint hits y-axis first (5 < 8) |
| Intersection | Where both constraints are tight |

**Solving the intersection:**
$$2x + 4y = 20 \quad\Rightarrow\quad x = 10 - 2y$$
$$4(10-2y) + 3y = 24 \quad\Rightarrow\quad 40 - 5y = 24 \quad\Rightarrow\quad y = 3.2,\ x = 3.6$$

## Evaluating Profit at Each Corner

| Point (x, y) | Profit = 20x + 30y |
|---|---|
| (0, 0) | $0 |
| (6, 0) | $120 |
| (0, 5) | $150 |
| **(3.6, 3.2)** | **$168** |

## Result

The optimal solution (allowing fractional/continuous production, e.g., averaged over time) is:

**x = 3.6 chairs, y = 3.2 tables → Maximum profit = $168**

Both resources are fully used at this point:
- Labor: 2(3.6) + 4(3.2) = 7.2 + 12.8 = 20h ✓
- Wood: 4(3.6) + 3(3.2) = 14.4 + 9.6 = 24kg ✓

**If chairs and tables must be whole numbers** (a more realistic factory constraint), the best integer solution is:

**x = 2 chairs, y = 4 tables → Profit = $160**
(Labor used: 20h; Wood used: 20kg — labor is the binding constraint here.)

I checked nearby integer points (3,3), (4,2), (4,3), (1,5) and none beat $160 while staying feasible.