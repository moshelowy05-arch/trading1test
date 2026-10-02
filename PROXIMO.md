# PROXIMO — prediction-arb

Read this first when opening a session in this project.

## Current state (2026-10-01)
Hard arbitrage was exhausted (no economically meaningful edge on public data). The statistical research phase,
study 1 (Kalshi calibration), is running on branch `research/calibration-study`: harness built and reviewed (439
tests), pre-registrations frozen in text, window approved (Apr–Aug 2026, K = 14, 57,069 markets). Downloads run
unattended at ~4 requests/s; `scripts/research/overnight.sh` builds the dataset, runs the train/validation checks and
fits the trading rule, then stops for the user. Nothing is frozen or unsealed yet. Live trading stays disabled.
Detail in the [handoff of 2026-10-01](handoffs/2026-10-01.md).

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
4. Model B as Study 2: freeze its rules and forward-score each new S3 day (cloud, keyless), especially after
   2026-10-13 (the VIP ends). Run `uv run python handoffs/2026-10-02/deep_book_probe.py` on the Mac now and weekly.
5. User decisions pending: API keys (self-serve, read-only first), an always-on server, a CPA opinion, and later
   whether to run a tiny live probe. Live trading stays disabled until the user explicitly decides.

## Previous handoffs
- [2026-10-02 markets / market making / fat-finger / assumptions](handoffs/2026-10-02-markets-mm-fatfinger-assumptions.md)
- [2026-10-01 strategy review](handoffs/2026-10-01-strategy-review.md)
- [2026-10-01](handoffs/2026-10-01.md)
