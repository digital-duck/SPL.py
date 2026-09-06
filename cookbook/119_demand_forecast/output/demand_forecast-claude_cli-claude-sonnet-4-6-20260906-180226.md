# SPL Run: demand_forecast

- **Adapter:** claude_cli
- **Model:** claude-sonnet-4-6
- **Tokens:** 344 in / 337 out
- **Latency:** 27626ms
- **Timestamp:** 2026-09-06 18:02:26

## Output

```output
=== Demand Forecasting (solver=ON / statsmodels UnobservedComponents) ===

Problem:
Use the default 36-month widget sales dataset.

Forecast (6 periods ahead):
| Period | Forecast | Lower 95% | Upper 95% |
|---|---|---|---|
| +1 | 182.7 | 158.7 | 206.6 |
| +2 | 191.2 | 164.9 | 217.4 |
| +3 | 212.9 | 184.1 | 241.6 |
| +4 | 205.1 | 173.8 | 236.3 |
| +5 | 205.0 | 171.1 | 238.9 |
| +6 | 219.9 | 183.4 | 256.3 |

Hold-out RMSE: **10.00** vs naïve baseline 19.76 (✓ beats naïve)

Interpretation:
**Demand is on a clear upward trend**, rising from ~183 units in month +1 to ~220 by month +6 — roughly a 20% increase over the horizon. A seasonal pulse is visible: demand jumps sharply at +3 (likely a quarterly or seasonal peak, perhaps end-of-quarter), eases slightly at +4/+5, then climbs to a new high at +6, suggesting a repeating 3-month cycle. **For inventory planning: build safety stock ahead of months +3 and +6**, where demand spikes; a minimum replenishment target of ~215 units per cycle would cover the trend with buffer. The model earns confidence — RMSE of 10 is half the naïve baseline's error, so the point forecasts are a reliable anchor for ordering decisions. **Uncertainty does widen as the horizon extends**: the 95% interval is ~48 units wide at +1 but grows to ~73 units by +6 (roughly ±16% of forecast), so hold tighter commitments for near-term orders and maintain flex capacity or supplier options for months +5/+6 to hedge the broader cone.

LLM calls: 2
```
