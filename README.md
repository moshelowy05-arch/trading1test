# pmarb

A research and (disabled-by-default) execution platform for testing, on real data, whether two prediction-market
arbitrage ideas survive fees, depth, latency, partial fills and settlement differences:

- **Strategy A** — cross-venue: Kalshi ↔ Polymarket US on economically matched US sports contracts (Polymarket
  international is recorded for research only: it is not available to US persons).
- **Strategy B** — Kalshi logical inconsistencies inside one event (threshold ladders, range buckets).

```bash
cd ~/prediction-arb
uv sync
uv run pytest -q
uv run pmarb discover -v 5        # what exists, what matches, what blocks execution
uv run pmarb run                  # live data -> scanner -> paper + shadow, terminal dashboard (never live)
uv run pmarb backtest --hours 6   # gap analysis + replay over the data you recorded (clipped to corrected data)
```

`uv run` finds the project from the **current directory**: run these from the repository root (`cd ~/prediction-arb`), or from anywhere with `uv run --project ~/prediction-arb pmarb ...`. From a directory without a `pyproject.toml` (e.g. `~`), uv has no project environment and fails with "Failed to spawn: `pmarb`". `python -m pmarb` is equivalent to the `pmarb` script.

Start with [docs/FINAL_REPORT.md](docs/FINAL_REPORT.md) and [docs/RESEARCH_FINDINGS.md](docs/RESEARCH_FINDINGS.md).
Everything else: [architecture](docs/ARCHITECTURE.md) · [strategies](docs/STRATEGIES.md) ·
[risk](docs/RISK.md) · [API setup](docs/API_SETUP.md) · [operations](docs/OPERATIONS.md) ·
[testing](docs/TESTING.md) · [backtesting](docs/BACKTESTING.md) · [limitations](docs/LIMITATIONS.md).

Not investment advice. Live trading is disabled by default and guarded by multiple independent safeguards; the
authors of this code have never sent a live order with it.
