# SPL Run: data_quality

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 265 in / 1180 out
- **Latency:** 38587ms
- **Timestamp:** 2026-09-06 18:45:56

## Output

```output
=== Data Quality Validator (r103) | solver=OFF ===

── LLM Sample-Based Analysis ───────────────────────────────
## Data Quality Analysis — Sales Transactions Dataset

**Context:** 500 rows, 4 regions, 6 months, sourced from POS systems (implying multiple physical ingestion points).

---

### 1. Rules Likely Satisfied

| Rule | Basis |
|------|-------|
| `region` constrained to 4 values | POS systems are typically configured per-region; enumeration drift is less likely if software enforces it at entry |
| `transaction_id` format exists | POS systems generate IDs automatically — structural presence is expected |

These are *optimistic* assumptions, not confirmations. They require programmatic validation.

---

### 2. Rules at Risk of Violation

**`transaction_id` — uniqueness**
- Risk: **Medium-high.** Multi-region POS imports are a classic source of ID collisions. Each system may generate IDs independently (e.g., sequential integers starting at 1 per terminal). A cross-region merge without a namespace prefix will produce duplicates.
- Signal: The description says "imported from POS systems across 4 regions" — this is exactly the scenario where ID collision occurs.

**`amount` — not null, > 0, ≤ $10,000**
- Risk: **High.** Three distinct failure modes:
  - *Nulls:* failed/voided transactions often land as NULL rather than being dropped
  - *Negative values:* returns and refunds recorded as negative amounts rather than a separate record type
  - *Zero values:* test transactions, $0 loyalty redemptions, or initialization rows
  - *> $10,000:* high-value B2B or bulk orders may legitimately exceed the cap, or the cap may not be enforced at the POS level
- 6 months of data from 4 regions increases the surface area for all of these.

**`customer_id` — not null**
- Risk: **Medium.** Walk-in / guest / cash transactions may not capture a customer ID. POS systems often allow anonymous sales. With 500 rows over 6 months across 4 regions, some guest transactions are plausible.

**`region` — enumeration validity**
- Risk: **Low-medium.** Free-text entry or ETL mapping errors can introduce variants (`"north"`, `"N"`, `"Northeast"`, `NULL`). If the POS-to-database ETL has no validation step, this can slip through.

---

### 3. Estimated Rows with Quality Issues

These are order-of-magnitude estimates based on typical POS data quality rates, not computed from the actual data.

| Issue | Estimated Affected Rows | Reasoning |
|-------|------------------------|-----------|
| Duplicate `transaction_id` | 5–30 | Even 1–2 ID collisions per region per import cycle compounds |
| `amount` null or ≤ 0 | 10–40 (2–8%) | Voided/returned/test transactions; industry baseline ~3–5% |
| `amount` > $10,000 | 1–10 | Rare but plausible for bulk orders |
| `customer_id` null | 15–50 (3–10%) | Guest transactions; heavily depends on business type |
| `region` invalid value | 2–15 | ETL mapping; lower risk if automated |

**Total rows with at least one issue: rough estimate 30–100 (6–20% of 500).** This range is wide because the description gives no information about the ETL pipeline's maturity or existing validation.

---

### 4. Recommended Actions by Issue

**Duplicate `transaction_id`**
- Deduplicate by grouping on `(transaction_id, region)` — if the collision is cross-region, prepend the region code to create a composite key.
- Flag any true duplicates (same region, same ID) for source-system investigation.
- Add a unique constraint at the database level going forward.

**`amount` nulls**
- Investigate whether null amounts correspond to voided transactions. If so, exclude them from sales analysis but retain in an audit table.
- Do not impute — nulls here carry semantic meaning.

**`amount` ≤ 0**
- Negative values: determine if these are refunds. If so, model them as a separate `refund` record type, not negative sales.
- Zero values: treat as test or loyalty rows; remove from revenue aggregations.

**`amount` > $10,000**
- Pull these rows and verify against source receipts. If legitimate, adjust the business rule ceiling or add a flag column (`is_high_value`).
- Do not silently drop — a $15,000 transaction may be valid.

**`customer_id` nulls**
- Assign a sentinel value (e.g., `GUEST-{region}-{date}`) to preserve row count integrity without losing analytical granularity.
- Never drop these rows — they represent real sales volume.

**`region` invalid values**
- Normalize to the canonical four values via a lookup/mapping table in the ETL layer.
- Rows with unmappable region values should be quarantined and routed back to the source team for correction, not silently dropped or assigned a default.

---

**Priority order:** `transaction_id` duplicates → `amount` violations → `customer_id` nulls → `region` normalization. Fix ID integrity first because downstream aggregations depend on it.

Note: LLM inspects the description only — run with --param use_solver=true
to validate all rows with the expectation engine.
```
