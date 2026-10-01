# pmarb — prediction-market arbitrage research platform

Python 3.11 (uv). Researches whether (A) Kalshi ↔ Polymarket US cross-venue sports arbitrage and (B) Kalshi ladder
inconsistency arbitrage are profitable after fees, depth, latency, partial fills and settlement differences.
Economic truth over elegance: no midpoint pricing, no assumed fills, no hard-coded fees, fail closed.

## Commands (run from the repo root; elsewhere use `uv run --project ~/prediction-arb ...`)
- `uv sync` — install; `uv run pytest -q` — unit tests (network tests: `-m network`)
- `uv run ruff check src tests scripts` — lint (must pass); `uv run mypy` — strict types (must pass)
- `uv run pmarb discover -v 5` — one-shot discovery + matching summary
- `uv run pmarb run [--headless] [--modes paper,shadow]` — collector + scanner + paper/shadow + dashboard (never live)
- `PMARB_CONFIG=config/paper_research.toml uv run pmarb run --headless` — paper research overlay (accepts tail settlement diffs)
- `uv run pmarb backtest --hours 6 [--grid]` — gap analysis + execution replay over RECORDED data → docs/research/;
  clipped to `[backtest].valid_data_since` (pre-fix data is invalidated; `--include-invalidated` only for audits)
- `uv run pmarb collect` (data only) · `uv run pmarb web` (127.0.0.1:8765 history dashboard)
- `uv run pmarb status` / `pmarb kill` / `pmarb unhalt <mode> <scope> <key>`
- `uv run python scripts/ladder_fee_table.py` — Strategy B fee research table
- `uv sync --extra research` — numpy for the statistical research phase only (never needed by the live pipeline)
- `uv run pmarb research <fetch-listing|window|sample|fetch-meta|fetch-candles|fetch-prints|build|describe|fit-trade|freeze|validate-trade|unseal>`
  — statistical research phase (calibration study); public read-only data, never trades; runbook in
  docs/OPERATIONS.md, design in docs/superpowers/specs/2026-09-30-statistical-research-calibration-design.md

## Layout (src/pmarb)
core (money/enums/clock/ids) · marketdata (OrderBook) · venues/{kalshi,polymarket,polymarket_us} (API + parsers only)
· instruments (MarketInfo, teams) · payoff + relationships (payoff algebra, logical relations) · matching (rules,
sports equivalence) · fees (versioned engine; config/fees) · strategies (ladder = B, cross_venue = A) · scanner
(catalog, lifecycle) · collect (discovery, recorder) · execution (state machine, coordinator, gateways, live guard)
· risk · simulation (paper gateway) · shadow · replay + backtest · monitoring (terminal + web dashboards)
· persistence (SQLite, migrations/) · research (statistical studies; isolated from the live pipeline, never trades).

## Rules
- Venue-specific code stays in `venues/*` and `execution/gateways/*`; strategies see only `MarketInfo`/`OrderBook`.
- Money is `Decimal`. Prices come from depth walks. Fees only via `FeeEngine` (sources in config/fees/*.toml).
- Contract meaning comes from structured fields (strike_type/floor/cap, sports line + long side), never titles.
  Polymarket US spread titles describe the SHORT side on positive lines — structured fields win.
- Unknown settlement/fee/relationship ⇒ reject. Missing risk limit ⇒ ConfigError. Never weaken these for convenience.
- Uncertain order state (timeout, transport error, unparseable response) ⇒ UNKNOWN → reconcile → halt. Never assume.
- Polymarket US public gateway is CDN-cached (≤30 s): books are back-dated by the HTTP Age header. Replay fires a
  book at its RECEIVE time (stored stamp + source_age_ms), never at the back-dated stamp (look-ahead).
- In-play, a book unchanged at source (venue timestamp) > max_inplay_source_idle_ms is not executable.
- Live trading: off by default; requires config + LIVE_TRADING + PMARB_LIVE_CONFIRM + allowed venue + no kill switch.
  International Polymarket is never tradable (US person, NJ). Never log or commit secrets (.env is gitignored).
- Never fabricate data: tests use labelled fixtures (tests/fixtures, captured 2026-09-29) or synthetic factories.
- Update PROJECT_STATUS.md and project_state.json at milestones; commit with meaningful messages.

## Key docs
docs/RESEARCH_FINDINGS.md (verified mechanics, disproven premises) · docs/research/*.md (sources) ·
docs/ARCHITECTURE.md · docs/STRATEGIES.md · docs/RISK.md · docs/LIMITATIONS.md · docs/FINAL_REPORT.md
