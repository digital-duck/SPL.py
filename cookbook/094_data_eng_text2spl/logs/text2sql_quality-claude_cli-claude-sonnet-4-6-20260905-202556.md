# SPL Run: text2sql_quality

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 255 in / 150 out
- **Latency:** 8451ms
- **Timestamp:** 2026-09-05 20:25:56

## Output

```output
**Question:** What is the average order amount for customers in the Enterprise segment?

**Step 1 — Identify Enterprise customers.** Filtering `customers` on `segment = 'Enterprise'` yields customer id 1 (Acme Corp) and id 2 (Globex Inc).

**Step 2 — Find their orders.** Joining to `orders` on `customer_id IN (1, 2)` selects three rows:

| order id | customer_id | amount |
|----------|-------------|--------|
| 1 | 1 | 5000.00 |
| 2 | 1 | 7000.00 |
| 3 | 2 | 6000.00 |

**Step 3 — Aggregate.** Sum = 5000 + 7000 + 6000 = 18 000. Count = 3 orders. Average = 18 000 ÷ 3 = 6 000.

Final answer: 6000.00
```
