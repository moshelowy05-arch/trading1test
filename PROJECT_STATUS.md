# Project status

_Last updated: 2026-10-01 ~05:40 UTC (statistical research harness built; study not yet run). Tests: 416 passing; ruff and strict mypy clean._

## Phase checklist
| # | Phase | Status |
|---|---|---|
| 1 | Repository inspection | done (new repo `~/prediction-arb`, macOS arm64, uv, Python 3.11) |
| 2 | Research & validation | done (docs/research/*.md, docs/RESEARCH_FINDINGS.md; open questions listed there) |
| 3 | Architecture & data model | done (docs/ARCHITECTURE.md, migrations/0001_init.sql) |
| 4 | Market data adapters | done: Kalshi REST (+auth), Polymarket US gateway, Polymarket intl read-only. WS: not implemented (needs keys) |
| 5 | Normalisation & matching | done: payoff-proof matcher, rule profiles with sources, adversarial tests |
| 6 | Fee engine | done: versioned, matches published tables for all three venues |
| 7 | Cross-venue detector | done: taker-taker + maker-taker, sequential risk metrics |
| 8 | Ladder detector | done: nested pairs + partitions, declared precision for ranges |
| 9 | Collection & research DB | done, **recording live since 2026-09-29 05:30 UTC** |
| 10 | Paper trading | done (conservative simulator); running live |
| 11 | Execution simulator | done (latency, depth, partial fills, queue model, liquidity depletion) |
| 12 | Risk management | done (fail-closed limits, persisted halts, kill switch, auto-halts) |
| 13 | Monitoring | terminal dashboard done; web dashboard not built |
| 14 | Backtesting & stats | done (gap analysis, replay with simulated-time scheduler, sensitivity grid) |
| 15 | Shadow execution | done (exact payload capture + follow-ups); running live |
| 16 | Live infra (disabled) | done: Kalshi V2 + Polymarket US gateways behind LiveGuard; untested against venues |
| 17 | End-to-end validation | done on the corrected window (final backtest, paper/shadow); pipeline keeps recording |
| 18 | Reviews | done: 4 reviews (session 3) + an independent false-positive review (session 4); all confirmed issues fixed |
| 19 | Statistical research, study 1 (calibration) | harness built on branch `research/calibration-study` (CLI + docs); **study not yet run** |

## Statistical research, study 1 (calibration): harness built, study not yet run
- **What it is:** a research-only phase (`pmarb research ...`) asking whether Kalshi prices are calibrated, with two
  pre-registered hypotheses: `calibration_v1` (descriptive) and `calibration_trade_v1` (a trading rule evaluated
  under a declared hypothetical execution model). It never trades, uses public read-only endpoints only, and is
  isolated from the live pipeline (`pmarb.research` imports none of it; only `pmarb/cli.py` imports it, lazily).
- **Built (branch `research/calibration-study`, not merged):** resumable history fetch, date-aware fee model, window and
  sampling rules, dataset build with a sealed final-test file, statistics, both analyses, freeze/validate/unseal with
  an audit ledger, the `pmarb research` CLI, and docs. 416 tests pass (164 in `tests/unit/research`); ruff and strict
  mypy are clean. numpy is an optional extra: `uv sync --extra research`.
- **Not done:** nothing has been fetched, built or unsealed. No study result exists. The runbook is in
  docs/OPERATIONS.md (user checkpoints at the window, the fitted trading rule, and each unseal); the stated
  limitations are in docs/LIMITATIONS.md ("Statistical research phase").
- Spec: docs/superpowers/specs/2026-09-30-statistical-research-calibration-design.md. The live paper/shadow pipeline
  is unaffected.

## Verdict (session 4, corrected data 2026-09-29 19:03:22Z → 2026-09-30 00:22:18Z, 5.32 h)
**No arbitrage demonstrated; both strategies unprofitable on the evidence; live trading stays disabled.**
- Strategy A (Kalshi ↔ Polymarket US):
  - 7,432 fresh samples; one instant (2 samples) net-positive by +0.3¢/contract ($0.03 at 10, below min profit).
  - The 27 that would have been net-positive were all on Polymarket US books frozen at source 89 s–28 min in-play
    (excluded; sensitivity in FINAL_REPORT §8).
  - Replay: no fills in 10 of 11 scenarios; with a 0¢ hedge buffer, 1 fill, hedge failed, −$0.24. Paper/shadow: 1 fill, failed hedge, **−$1.12**.
- Strategy B (Kalshi ladders): 873,640 nested checks with **0 gross-positive**; 4,722 consistent
  partition states with **0 net-positive** (best −0.5¢/set).
- Blocker: authenticated real-time data (the public Polymarket US feed is CDN-cached, mean 19.7 s, and can be
  frozen in-play).

## The four remaining gaps (2026-09-30, after Step 2)
- **v2 rules template** (full-ladder family only; Strategy B's v1 is verified byte-identical): rungs in ladders
  53,579 → 54,472, outlier rungs 931 → 322.
- **`cross_event` family:** same-observation proof (primary text + expiration + close + sources) with
  path-dependence guards. It links 45 event pairs per sweep.
  - First confirmed survivor of the project: SCFI "≥ 5,000" vs "> 5,000" (same final print), **+$0.04**, bounded,
    persistent.
  - Economically meaningless; the verdict is unchanged.
- **Sub-second:**
  - The Kalshi WebSocket client is built: sequence-gap safe, off until operator keys, untested against the venue.
  - The 1-s in-play fast lane is on.
- **Polymarket US real-time:** not implemented. It needs keys, NJ eligibility, and a schema we must not guess.
- Pipeline restarted on this code at 2026-09-30T06:21:10Z (no halts; live disabled).

## Step 2 (2026-09-30): exhausting hard, logically provable arbitrage — Traditional Arbitrage V1 candidate
- **New families**, each separately identifiable and evaluated by the same scanner, risk engine and state machine
  (paper/shadow; live disabled): `within_game`, `multi_outcome` ("exactly one wins", with a formal outcome-set
  analysis), `ladder_series` (every threshold/range event; NO subsets; replication identities; template-split
  events). Classes: guaranteed / bounded / replication / no arbitrage / invalid data / liquidity / edge / unknown
  settlement / unknown relationship. There is an executable-size profile for every construction.
- **Universe sweeps.** Every open Kalshi event (≈12.7k events / 121.5k markets) is swept every 10 min: screen →
  live confirmation, one request per event. **7 sweeps: 495 screen candidates, 491 confirmed, 0 survived fees**
  (all one-tick overrounds; best −0.12¢/set).
- **10 h standard backtest** (corrected data):
  - Strategy B: 2.72 M nested checks, 0 gross-positive.
  - Strategy A: 4 net-positive instants, best +3.1¢ (a stale quote after a scoring play; not filled in replay).
  - Within-game: 5 samples, ≤ +0.5¢/set.
  - Families on recorded books: 0 net-positive.
  - Replay: 0 fills in all 12 scenarios.
- **Strategy A/B invariance proven.** The pre-Step-2 code and the current code give byte-identical Strategy A/B
  output on one frozen DB snapshot.
- **Correctness fixes found on the way:**
  - duplicate snapshots double-counted cross-venue samples;
  - categorical markets (strike_type structured/custom) were routed to the ladder path;
  - "equal number of wins … 50/50" tie wording was missed;
  - half-splits with more than 2 outcomes are unsafe;
  - Strategy B's scope must be its own fixed series list (KXETHD).
- **Verdict (FINAL_REPORT §8b):** for taker execution on public Kalshi data the hard-arbitrage universe is
  effectively exhausted. Unsearched: sub-poll latency windows (need WebSockets), Polymarket US baskets (unconfirmable),
  cross-event relations (unprovable), 1.5% of rungs lost to template collisions.
- The pipeline was restarted on the final Step 2 code at 2026-09-30T05:54:34Z (no halts; live disabled).

## Session 5 (2026-09-30): within-game relationships and coverage
- New scan `scripts/game_relations.py` (also in every backtest report). It checks moneyline/spread/total logical
  relationships within Kalshi, within Polymarket US and mixed, on recorded data.
  - About 480k executable-grade checks. Gross gaps appear only as exactly one tick.
  - 3 net-positive samples, +0.06¢ to +0.5¢ per contract, at end-of-game extreme prices, each shorter than one poll.
  - Economically negligible. See docs/research/GAME_RELATIONS.md.
- **Bug fixed:** replay and the gap analyses applied one fetch's books one at a time, which made fake same-venue
  gaps (a fake 28¢ NHL moneyline gap). They are now applied per fetch. Live was unaffected.
- **Coverage:** the collector now polls every discovered Kalshi game market (470, of which 109 were never recorded
  before), one request per game. The pipeline was restarted at 2026-09-30 01:08:12Z.
- **Next coverage steps:** multi-outcome events (futures, awards, elections) with buy-every-outcome checks; all
  events of each ladder series.

## Session 4 (2026-09-29/30)
- **`Failed to spawn: pmarb`:** the command was run from `~`, where uv finds no project. The package was fine.
  - A relative `PMARB_CONFIG` now resolves from any cwd, config errors exit 2, and `python -m pmarb` works.
  - Docs say to run from the repo root.
- **Backtests clip to `[backtest].valid_data_since`** (19:03:22.774Z), so invalidated pre-fix data is never mixed
  in. `--include-invalidated` exists for audit only.
- **Fixed false-positive sources**, all with regression tests:
  - replay look-ahead on CDN-aged books;
  - the arrival-book rule;
  - Strategy B partitions never built (tokenizer and comparator bug; the fee script was empty for that reason, not
    for lack of data);
  - in-play frozen-book guard;
  - resting orders filled by pre-existing trades;
  - repeated trade-through fills;
  - resting on Polymarket US;
  - taker ledger released too early;
  - trading-close, venue-state and ladder-skew checks.
- The live pipeline was restarted on the final code at 2026-09-30T00:23:13Z.

## Session 3 highlights
- The Polymarket US public gateway is **CDN-cached for up to 30 s**. Books are now back-dated by the `Age` header
  (migration 0002).
- The only "profitable" cross-venue window was a stale-cache artifact. All ladder "violations" were cross-request
  snapshot artifacts; ladder rungs are now fetched per event.
- Review fixes: execution safety, API correctness, simulator realism, security hardening. The code is clean under
  strict mypy, with 143 tests passing.
- The pre-fix paper P&L ($4.74 on 5 fills) is invalidated.

## Next
1. Keep live trading disabled.
2. With API keys: authenticated WebSockets (Kalshi, then Polymarket US if NJ-eligible). Answer the frozen-book
   question (paused vs executable). Run shadow mode for several weeks across sports and game states.
3. Re-run `PMARB_CONFIG=config/paper_research.toml uv run pmarb backtest --hours 24 --grid` (from the repo root) as
   corrected data accumulates. Re-run `scripts/ladder_fee_table.py` across more ladder cycles.
4. Remaining open items: docs/LIMITATIONS.md ("Known open items").
