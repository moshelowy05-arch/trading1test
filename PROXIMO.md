# PROXIMO — prediction-arb

Read this first when opening a session in this project.

## Current state (2026-10-01)
Hard arbitrage was exhausted (no economically meaningful edge on public data). The statistical research phase,
study 1 (Kalshi calibration), is running on branch `research/calibration-study`: harness built and reviewed (439
tests), pre-registrations frozen in text, window approved (Apr–Aug 2026, K = 14, 57,069 markets). Downloads run
unattended at ~4 requests/s; `scripts/research/overnight.sh` builds the dataset, runs the train/validation checks and
fits the trading rule, then stops for the user. Nothing is frozen or unsealed yet. Live trading stays disabled.
Detail in the [handoff of 2026-10-01](handoffs/2026-10-01.md).

## HANDOFF 2026-10-02 → read handoffs/2026-10-02-HANDOFF.md first (local-session checklist, guardrails, road map)
Important: all Model B dollar figures are provisional. About half rest on estimated (last-trade) settlement values;
re-score with official results on the Mac (handoffs/2026-10-02/model_b_forward.py) before relying on them.

## Update 2026-10-02 (cloud session; see handoffs/2026-10-02-markets-mm-fatfinger-assumptions.md)
- Every Kalshi trade for 8 days (public S3 tape, 102M trades) was censused. About 61% of premium ($290M/day) sits in
  categories the project never examined (15-min crypto, combos, lower-tier tennis, 15-min commodities).
- Two-sided market making is not a retail edge (adverse selection at retail speed). The 2026-10-01 primary (a slow
  non-sports maker) is withdrawn: 0.85% of premium, paid professionals present, and it loses on our tape.
- Fat-finger "Model B" is the only idea with a consistent positive signal. It rests standing 3c YES and NO bids in
  20-80c markets. It was positive on 58 of 59 test days across 9 windows (Jul 2025 to Oct 2026). This is a
  COUNTERFACTUAL from the trade tape; real fills, competition, an always-on canceller, API geofencing, Rule 5.11 and
  tax are all unresolved.
- Assumption audit: 135 nodes, 32 contradicted (handoffs/2026-10-02/assumption_tree.md). Key: "no API keys" is a
  choice, and the taker-first framing was the main blind spot.
- Study 1 downloads were at 19,600/152,984 candles at the last check (Mac). Closing the lid only pauses them.

## Next step
1. Check progress: `cd ~/prediction-arb && uv run python scripts/research/fetch_status.py` and
   `tail logs/research_overnight.out`. If the fetch chain is not running and not complete, restart it with the loop in
   `docs/OPERATIONS.md`.
2. When `docs/research/exploratory/train_tails.md` appears, show it to the user (exploratory, training months only).
3. When the runner reports "Checkpoint 2", show the fitted trading rule and wait for the user's approval before
   freezing. Ask again before unsealing. Before unsealing, verify the fee model (centicent rounding from 2026-05-28,
   per-series M, the 2026-07-03 index change, combo maker fees) and sub-cent price handling.
4. Model B: first re-score Sept 23-30 with official settlements (`model_b_forward.py`), then keep scoring each new day
   as a background record (not a gate). Run `uv run python handoffs/2026-10-02/deep_book_probe.py` once during the pilot.
5. Moshe decided (2026-10-02) to run a small live pilot of Model B (about one week, $25-50; plan in
   handoffs/2026-10-02/model_b_pilot_plan.md). He creates the API key and turns on live trading himself once the bot
   passes a demo test. Taxes are his own matter.

## Previous handoffs
- [2026-10-02 markets / market making / fat-finger / assumptions](handoffs/2026-10-02-markets-mm-fatfinger-assumptions.md)
- [2026-10-01 strategy review](handoffs/2026-10-01-strategy-review.md)
- [2026-10-01](handoffs/2026-10-01.md)
