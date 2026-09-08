# Resource Allocation Report

**Problem:** An IT department must select a portfolio of projects for next quarter. Six candidate projects are available. Project P1 costs $120K and requires 3 developer-months, delivering strategic value 8. Project P2 costs $80K and requires 2 developer-months, delivering value 5. Project P3 costs $200K and requires 5 developer-months, delivering value 10. Project P4 costs $150K and requires 3 developer-months, delivering value 9. Project P5 costs $60K and requires 2 developer-months, delivering value 4. Project P6 costs $90K and requires 2 developer-months, delivering value 6. The total budget is $500K and the team has 10 developer-months available. Each project is either fully funded or not funded - no partial investment. Select which projects to fund to maximize total strategic value.

## Solution

Here's a step-by-step mathematical analysis to determine the optimal project portfolio selection:

1. **Project Data:** We begin by organizing the data for each of the six projects into a table:

| Project | Cost ($) | Developer Months | Strategic Value |
|---|---|---|---|
| P1     | 120,000  | 3                 | 8                |
| P2     | 80,000   | 2                 | 5                |
| P3     | 200,000  | 5                 | 10               |
| P4     | 150,000  | 3                 | 9                |
| P5     | 60,000   | 2                 | 4                |
| P6     | 90,000   | 2                 | 6                |


2. **Search Space and Enumeration:** The total number of possible portfolio combinations is 2<sup>6</sup> = 64.  Due to the computational constraints of manual enumeration, we will use a structured approach focusing on projects with high value-to-cost ratios initially. We'll systematically evaluate subsets, starting with those that appear most promising and progressively exploring other possibilities by swapping in lower-value projects.

3. **Enumerating Candidate Subsets:**  We’ll consider the following subsets, evaluating their feasibility (budget & dev-months) and total value:

   * **Subset 1:** {P1, P2, P5}
      * Cost: $120K + $80K + $60K = $260K
      * Dev-Months: 3 + 2 + 2 = 7
      * Value: 8 + 5 + 4 = 17

   * **Subset 2:** {P1, P2, P3}
      * Cost: $120K + $80K + $200K = $400K  (Infeasible - exceeds budget)

   * **Subset 3:** {P1, P4, P5}
      * Cost: $120K + $150K + $60K = $330K
      * Dev-Months: 3 + 3 + 2 = 8
      * Value: 8 + 9 + 4 = 21

   * **Subset 4:** {P1, P4, P6}
      * Cost: $120K + $150K + $90K = $360K (Infeasible - exceeds budget)

   * **Subset 5:** {P2, P3, P5}
      * Cost: $80K + $200K + $60K = $340K (Infeasible - exceeds budget)

   * **Subset 6:** {P1, P5, P6}
       * Cost: $120K + $60K + $90K = $270K
       * Dev-Months: 3+2+2=7
       * Value: 8+4+6 = 18

   * **Subset 7:** {P2, P3, P6}
      * Cost: $80K + $200K + $90K = $370K (Infeasible - exceeds budget)

   * **Subset 8:** {P3, P4, P5}
       * Cost: $200K + $150K+ $60K = $410K  (Infeasible - exceeds budget)

    * **Subset 9:** {P1, P2, P3, P5}
        * Cost: $120K + $80K + $200K + $60K = $460K (Infeasible – exceeds Budget.)

   * **Subset 10:** {P1, P2, P3, P4} -  (too expensive)

    * **Subset 11:** {P1, P2, P4, P5}
      * Cost: $120K + $80K + $150K+ $60K =$410K (Infeasible - exceeds budget)


   * **Subset 12:** {P3, P4, P5, P6} -  (too expensive)

   * **Subset 1

## Run Metrics

| Metric | Value |
|---|---|
| Mode | solver=OFF (LLM reasoning only) |
| LLM calls | 2 |
| Stage 1 — direct LLM solve (s) | 18.60 |
| Stage 2 — interpretation (s) | — |
| Total latency (s) | 25.40 |
| Input tokens | 1,894 |
| Output tokens | 1,244 |
| Total tokens | 3,138 |