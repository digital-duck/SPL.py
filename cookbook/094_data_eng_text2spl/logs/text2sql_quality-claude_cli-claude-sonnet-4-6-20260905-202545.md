# SPL Run: text2sql_quality

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 466 in / 170 out
- **Latency:** 11935ms
- **Timestamp:** 2026-09-05 20:25:45

## Output

```output
# Text-to-SQL with Data-Quality Gates Report

**Question:** What is the average order amount for customers in the Enterprise segment?

**Verifier status:** `OK`
**Rows returned:** `1`
**Referential integrity:** `True`
**Two-independent-ways stat agreement:** `True` (AVG=6000.0, SUM/COUNT=6000.0)
**Row-level round-trip vs ground truth:** `match`

## Interpretation

**Question:** What is the average order amount for Enterprise-segment customers?

**Answer:** Enterprise customers place orders averaging **$6,000.00**. Both independent calculation methods returned identical results (`stat_a = stat_b = 6000.0`), and the row-level diff against the ground-truth query confirmed a perfect match.

**Why it matters:** The two-way recomputation and referential integrity check rule out calculation artifacts, broken joins, and data quality issues — so this $6,000 figure can be used in production reporting with confidence.

Final answer: verified

## Generated SQL (LLM)

```sql
SELECT AVG(o.amount) FROM orders o JOIN customers c ON o.customer_id = c.id WHERE c.segment = 'Enterprise';
```
```
