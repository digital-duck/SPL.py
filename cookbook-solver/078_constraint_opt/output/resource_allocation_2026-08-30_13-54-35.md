# Resource Allocation Report

**Problem:** An IT department must select a portfolio of projects for next quarter. Ten candidate projects are available. Project P1 costs $80K and requires 2 developer-months, delivering strategic value 6. Project P2 costs $120K and requires 3 developer-months, delivering value 9. Project P3 costs $60K and requires 2 developer-months, delivering value 5. Project P4 costs $150K and requires 4 developer-months, delivering value 11. Project P5 costs $200K and requires 5 developer-months, delivering value 12. Project P6 costs $90K and requires 2 developer-months, delivering value 7. Project P7 costs $110K and requires 3 developer-months, delivering value 8. Project P8 costs $70K and requires 2 developer-months, delivering value 5. Project P9 costs $180K and requires 4 developer-months, delivering value 13. Project P10 costs $100K and requires 3 developer-months, delivering value 6. The total budget is $600K and the team has 15 developer-months available. Each project is either fully funded or not - no partial investment. Select which projects to fund to maximize total strategic value.

## Solution

1. **Project List:** We begin by listing all projects with their cost, developer-month requirement, and strategic value:

| Project | Cost (K$) | Dev-Months | Value |
|---|---|---|---|
| P1      | 80        | 2          | 6    |
| P2      | 120       | 3          | 9    |
| P3      | 60        | 2          | 5    |
| P4      | 150       | 4          | 11   |
| P5      | 200       | 5          | 12   |
| P6      | 90        | 2          | 7    |
| P7      | 110       | 3          | 8    |
| P8      | 70        | 2          | 5    |
| P9      | 180       | 4          | 13   |
| P10     | 100       | 3          | 6    |


2. **Search Space & Enumeration:** The total number of possible project subsets is 2^10 = 1024.  However, we can significantly reduce this by prioritizing projects with a high value-to-cost ratio (Value/Cost). A systematic approach involves starting with the highest ratio projects and building up potential portfolios.

   * **Initial Consideration:** Projects P9 and P5 have the highest initial value-to-cost ratios:
      * P9: 13 / 180 = 0.072
      * P5: 12 / 200 = 0.06
   *  We'll start by considering combinations including these high ratio projects and then evaluate other options.

3. **Enumeration of Candidate Subsets:** We systematically explore subsets, evaluating budget and developer-month constraints at each step. Here are some candidate subsets and their evaluations:

    * **Subset 1 (High Value Focus):** P9 + P5 = 13 + 12 = 25. Cost = 180 + 200 = 380K, Dev-Months = 4 + 5 = 9.  Value = 13 + 12 = 25. *Infeasible* due to exceeding the budget (380K > 600K).

    * **Subset 2:** P9 + P7 = 13 + 8 = 21. Cost = 180 + 110 = 290K, Dev-Months = 4 + 3 = 7. Value = 13 + 8 = 21. *Infeasible* due to exceeding the budget (290K > 600K).

    * **Subset 3:** P5 + P7 = 12 + 8 = 20. Cost = 200 + 110 = 310K, Dev-Months = 5 + 3 = 8. Value = 12 + 8 = 20. *Infeasible* due to exceeding the budget (310K > 600K).

    * **Subset 4:** P4 + P7 = 11 + 8 = 19. Cost = 150 + 110 = 260K, Dev-Months = 4 + 3 = 7. Value = 11+8=19. *Infeasible* due to exceeding the budget (260K > 600K).

    * **Subset 5:** P9 + P6 = 13 + 7 = 20. Cost = 180 + 90 = 270K, Dev-Months = 4 + 2 = 6. Value = 13 + 7 = 20. *Infeasible* due to exceeding the budget (270K > 600K).

    * **Subset 6:** P5 + P6 = 12 + 7 = 19. Cost = 200 + 90 = 290K, Dev-Months = 5 + 2 = 7. Value = 12+7=19. *Infeasible* due to exceeding the budget (290K > 600K).

    * **Subset 7:** P4 + P6 =

## Run Metrics

| Metric | Value |
|---|---|
| Mode | solver=OFF (LLM reasoning only) |
| LLM calls | 2 |
| Stage 1 — direct LLM solve (s) | 20.10 |
| Stage 2 — interpretation (s) | — |
| Total latency (s) | 32.30 |
| Input tokens | 2,068 |
| Output tokens | 1,492 |
| Total tokens | 3,560 |