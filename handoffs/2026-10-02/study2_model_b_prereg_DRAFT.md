# Study 2 — Model B (standing 3c bids) — DRAFT pre-registration

**Status: DRAFT. Not frozen. The rules below become binding only after Moshe approves them and they are recorded in
pmarb's pre-registration format (research/prereg) with a hash in the audit ledger.**

## Question
Do standing 3c YES and 3c NO bids, rested in Kalshi markets currently trading 20–80c, make money once valued with
Kalshi's **official settlement results**? Do real orders get the fills the public trade tape implies?

## Why this is a study and not yet a strategy
- Every result so far is a counterfactual from Kalshi's public trade file: it shows trades, not order books, not who
  initiated, and not results.
- About half of the simulated profit in September was valued with an estimated settlement (the last trade), not an
  official result.
- That estimate is ambiguous when a market's final second holds several prices. On 2026-09-26 it alone changed the
  day's result by about 20%.

## Phase A — forward test on public data (free, no API key, no orders)

**Rules (frozen in `handoffs/2026-10-02/model_b_forward.py`)**
- One YES bid at 3c and one NO bid at 3c (i.e. a YES ask at 97c), 100 contracts each, held to settlement.
- A side is eligible while the market's volume-weighted price over the prior 600 s is 20–80c, with at least 3
  trade-seconds. Fills count only while eligible, which assumes orders are cancelled when a market leaves the band.
- After a fill, that side waits 600 s before it can fill again.
- Combo series (KXMVE*) are excluded.
- Fill size = min(100, max(0, beyond − C) + s × at), where:
  - beyond = contracts that traded strictly through 3c in that second;
  - at = contracts that traded exactly at 3c.
- Variants:
  - **through** (s = 0, C = 0) is the PRIMARY. It does not depend on queue position.
  - base: s = 0.10.
  - c30 and c100: s = 0 with 30 / 100 extra competitor contracts ahead of us.
- Settlement value: Kalshi's official `settlement_value_dollars` once a market is determined. Otherwise the last-trade
  estimate, reported separately.

**Forward window**
- 28 Eastern-time days from **2026-10-03** through **2026-10-30**.
- The rules were written on 2026-10-02. Earlier days have all been looked at and are excluded.
- The window spans the end of the Volume Incentive Program (no earlier than 2026-10-13); report before and after
  separately.

**Primary metric**
- Mean daily P&L (USD) of the `through` variant, using **official settlement values only**.
- Days are scored once at least 95% of that day's fill P&L has an official result. Re-run with `--force` until then.

**Decision rule**
- **PASS:** mean > 0 with a one-sided day-level t ≥ 2.0, AND the c30 variant's mean > 0.
- **FAIL:** anything else.
- Interim futility check after 14 days: if cumulative `through` P&L is ≤ 0, stop and record FAIL.

**Reported (not used for the decision)**
- base / c30 / c100 variants;
- sports vs non-sports split;
- share of P&L from the top 10 events;
- before vs after the end of the Volume Incentive Program.

**Retrospective re-score, done separately and labelled exploratory**
- Re-run the already-viewed windows (2026-08-10..17, 09-10..15, 09-16..22, 09-23..30) with official settlement values.
- These windows informed the design, so they cannot confirm it.
- If the re-score turns clearly negative, stop before Phase B.

## Phase B — do real orders fill? (needs a read-only API key; still no orders)
- Record authenticated order-book updates (WebSocket) for about 200 eligible markets for 1–2 weeks.
- At every sweep through 3c, check how much size rested at 3c–5c ahead of a hypothetical order and whether the market
  was paused or reopened.
- Run `handoffs/2026-10-02/deep_book_probe.py` weekly. Week 1 sets the baseline; a doubling of median resting size at
  2–5c is a competition warning.

## Phase C — tiny live probe (ONLY with Moshe's explicit approval; live trading is disabled by default)
- 1-contract orders at 3c on both sides in up to about 300 eligible markets. Worst case is 3c per fill; total money at
  risk of a few tens of dollars.
- Duration: 2–4 weeks.
- Compare real fills with the Phase A simulation for the same days and markets.
- **PASS:** real fills ≥ 50% of simulated through-fills, and real P&L per fill within the simulated range.
- Log every Rule 5.11 review, cancellation or repricing.

## Not allowed
- Changing any rule or threshold after seeing forward data. Any change makes a new study version with a new forward
  window.
- Moving to Phase C without Moshe's explicit approval, a CPA tax opinion, and a working cancel-on-exit mechanism
  (order expiries or an always-on server).
