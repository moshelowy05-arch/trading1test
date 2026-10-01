# PROXIMO — prediction-arb

Read this first when opening a session in this project.

## Current state (2026-10-01)
Hard arbitrage was exhausted (no economically meaningful edge on public data). The statistical research phase,
study 1 (Kalshi calibration), is running on branch `research/calibration-study`: harness built and reviewed (439
tests), pre-registrations frozen in text, window approved (Apr–Aug 2026, K = 14, 57,069 markets). Downloads run
unattended at ~4 requests/s; `scripts/research/overnight.sh` builds the dataset, runs the train/validation checks and
fits the trading rule, then stops for the user. Nothing is frozen or unsealed yet. Live trading stays disabled.
Detail in the [handoff of 2026-10-01](handoffs/2026-10-01.md).

## Next step
1. Check progress: `cd ~/prediction-arb && uv run python scripts/research/fetch_status.py` and
   `tail logs/research_overnight.out`. If the fetch chain is not running and not complete, restart it with the loop in
   `docs/OPERATIONS.md`.
2. When `docs/research/exploratory/train_tails.md` appears, show it to the user (exploratory, training months only).
3. When the runner reports "Checkpoint 2", show the fitted trading rule and wait for the user's approval before
   freezing. Ask again before unsealing.

## Previous handoffs
- [2026-10-01](handoffs/2026-10-01.md)
