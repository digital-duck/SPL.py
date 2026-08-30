# Resource Allocation Report

**Problem:** An IT department must select a portfolio of projects for next quarter. Six candidate projects are available. Project P1 costs $120K and requires 3 developer-months, delivering strategic value 8. Project P2 costs $80K and requires 2 developer-months, delivering value 5. Project P3 costs $200K and requires 5 developer-months, delivering value 10. Project P4 costs $150K and requires 3 developer-months, delivering value 9. Project P5 costs $60K and requires 2 developer-months, delivering value 4. Project P6 costs $90K and requires 2 developer-months, delivering value 6. The total budget is $500K and the team has 10 developer-months available. Each project is either fully funded or not funded - no partial investment. Select which projects to fund to maximize total strategic value.

## Solution

Here’s a step-by-step mathematical analysis to determine the optimal project portfolio selection:

1. **Project Data:** We begin by organizing the data for each project:

| Project | Cost (K$) | Dev-Months | Value |
|---|---|---|---|
| P1 | 120 | 3 | 8 |
| P2 | 80 | 2 | 5 |
| P3 | 200 | 5 | 10 |
| P4 | 150 | 3 | 9 |
| P5 | 60 | 2 | 4 |
| P6 | 90 | 2 | 6 |


2. **Search Space and Enumeration:**  With six projects, the total number of possible subsets is 2<sup>6</sup> = 64.  We’ll use a structured enumeration approach starting with projects offering the highest value-to-cost ratio to see if we can identify some potential high-value portfolios quickly. We will systematically examine all combinations and evaluate them against budget and team constraints.

3. **Enumerated Candidate Portfolios:** Let's consider several candidate portfolios:

   * **Portfolio 1 (P1, P2):**
      * Cost: 120K + 80K = 200K
      * Dev-Months: 3 + 2 = 5
      * Value: 8 + 5 = 13
   
   * **Portfolio 2 (P1, P3):**
      * Cost: 120K + 200K = 320K  (Infeasible - exceeds budget)

    * **Portfolio 3 (P1, P4):**
       * Cost: 120K + 150K = 270K
       * Dev-Months: 3 + 3 = 6
       * Value: 8+9=17

   * **Portfolio 4 (P1, P5):**
      * Cost: 120K + 60K = 180K
      * Dev-Months: 3 + 2 = 5
      * Value: 8 + 4 = 12

   * **Portfolio 5 (P1, P6):**
       * Cost: 120k+90k=210k
       * Dev-Months: 3+2=5
       * Value: 8+6=14

    * **Portfolio 6 (P2, P3):**
      * Cost: 80K + 200K = 280K (Infeasible - exceeds budget)

   * **Portfolio 7 (P2, P4):**
      * Cost: 80K + 150K = 230K
      * Dev-Months: 2+3 = 5
      * Value: 5 + 9 = 14

   * **Portfolio 8 (P2, P5):**
       * Cost: 80k + 60k=140k
       * Dev-Months: 2+2=4
       * Value: 5+4=9

    * **Portfolio 9 (P2, P6):**
      * Cost: 80K + 90K = 170K
      * Dev-Months: 2 + 2 = 4
      * Value: 5 + 6 = 11

   * **Portfolio 10 (P3, P4):**
       * Cost: 200k+150k=350k (Infeasible - exceeds budget)

    * **Portfolio 11 (P3, P5):**
      * Cost: 200K + 60K = 260K
      * Dev-Months: 5 + 2 = 7
      * Value: 10 + 4 = 14

    * **Portfolio 12 (P3, P6):**
       * Cost: 200k+90k=290k (Infeasible - exceeds budget)

   * **Portfolio 13 (P4, P5):**
      * Cost: 150K + 60K = 210K
      * Dev-Months: 3 + 2 = 5
      * Value: 9 + 4 = 1

## Run Metrics

| Metric | Value |
|---|---|
| Mode | solver=OFF (LLM reasoning only) |
| LLM calls | 2 |
| Stage 1 — direct LLM solve (s) | 17.50 |
| Stage 2 — interpretation (s) | — |
| Total latency (s) | 24.10 |
| Input tokens | 1,894 |
| Output tokens | 1,240 |
| Total tokens | 3,134 |