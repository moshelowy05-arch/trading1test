# Model B — small live pilot (about one week, $25–50)

**Moshe's decision (2026-10-02):** test Model B with a small amount of real money now. He accepts that it is
unproven, and he skips the long gated testing plan. Taxes are his own matter. This plan makes the pilot quick and keeps
losses capped.

## What the pilot can and cannot tell us
- **Can:** whether real 3c resting orders get filled the way the simulation says, whether anything breaks (rejected
  orders, reversed trades, location blocks), and roughly what each fill earns.
- **Cannot:** prove long-run profit in a week at this size. Gains and losses will be in cents to a few dollars and
  noisy. Scale only after the fills look real.

## The rules (same as the simulation; `model_b_forward.py` scores them)
- **Which markets:** every open market except combos (KXMVE*) whose 10-minute volume-weighted price is 20–80c, with at
  least 3 trade-seconds in those 10 minutes.
- **The two orders, per eligible market:**
  - **YES bid:** `side=bid`, `price="0.0300"`.
  - **NO bid:** `side=ask`, `price="0.9700"`. Selling YES at 97c is buying NO at 3c.
- **Size:** start at `count="0.10"` contracts; fractional contracts are allowed down to 0.01. Optionally `1.00` on a
  few hundred markets instead.
- **Order settings:**
  - `post_only=true`, so the bot never pays taker fees;
  - `time_in_force=good_till_canceled` with `expiration_time` 15 minutes ahead;
  - `cancel_order_on_pause=true`;
  - `self_trade_prevention_type=maker`;
  - all orders in one order group, used as an exposure cap.
- **Order upkeep:**
  - Renew the expiry about every 10 minutes while the market stays eligible. An expiry-only amend keeps queue priority
    (docs changelog, 2026-10-01).
  - Cancel at once when the market leaves 20–80c.
  - After a fill, wait 10 minutes before re-placing that side.
- **Holding:** hold every fill to settlement; no selling during the pilot.
- **Why 15-minute expiries:** when the Mac sleeps or the bot stops, every order dies within 15 minutes, so nothing is
  left behind.

## Money and limits (Moshe sets these; the bot enforces them and halts if any is hit)
- **Deposit $25–50.**
  - Resting orders reserve their cost: 0.1 contract × $0.03 × 2 sides × about 1,000 markets ≈ $6.
  - Filled positions also tie up cash until settlement, about $10–15 a day at 0.1 contract.
- **Daily loss stop:** for example $10. On hitting it, cancel everything and stop for the day.
- **Max money spent on fills per day:** for example $15.
- **Max contracts per market:** for example 1.
- **Max open orders:** for example 2,000.
- **Emergency stop:** `uv run pmarb kill` cancels everything.
- **Uncertain order state** (a timeout or an unparseable reply): reconcile, then halt. This is a project rule.

## Steps
1. **Moshe creates a Kalshi API key** at kalshi.com → Account → API Keys and saves the private key file where
   `docs/API_SETUP.md` says. Never paste the key into a chat; Claude never reads or prints it.
2. **Location attestation.** If the API refuses Sports, Elections or Entertainment orders, the key's location
   attestation has lapsed (`api_key_region_expiration_ts` in `GET /api_keys`). Run on the other categories meanwhile.
   How to renew the attestation is not documented in the API docs; check the Kalshi app or ask support.
3. **Day 1, sanity check (automatic, 1–2 hours of computer time).** Re-score Sept 23–30 with official settlement
   results:
   `uv run --with duckdb python handoffs/2026-10-02/model_b_forward.py --start 2026-09-23 --end 2026-09-30 --out logs/model_b_rescore.csv --prune`.
   If it comes back clearly negative, tell Moshe before he spends money. It is his call.
4. **Day 1–2, build the bot (Claude, a few hours) and test it on Kalshi's demo exchange** (fake money:
   `https://demo-api.kalshi.co/trade-api/v2`). Check that orders place, renew, cancel, respect the limits, and that the
   kill switch works.
   - Reuse pmarb's Kalshi V2 gateway, LiveGuard and risk modules.
   - Keep venue code in `venues/` and `execution/gateways/`.
   - Use `Decimal` for money.
5. **Day 2, go live.** Claude says when the bot is ready. **Moshe turns on live trading himself** (the config flag
   plus `LIVE_TRADING` and `PMARB_LIVE_CONFIRM`, per CLAUDE.md). Run while the Mac is awake; `caffeinate` helps.
6. **Days 2–7, daily check.**
   - Kalshi publishes each day's public trade file about a day later.
   - Compare real fills with simulated fills for the **same hours the bot was running**. The bot must log its active
     windows; restrict the simulation to them.
   - Report three things: real ÷ simulated fill count, P&L per fill, and any order rejections or reversed trades.
7. **Day 7, decide:**
   - **Scale up:** bigger size, more hours, maybe a small always-on server.
   - **Adjust**, or **stop**.
   - A good pilot means real fills are at least about half of the simulated fills for the same hours, with no
     surprises.

## Known risks
- **Unproven.** About half of the simulated profit rested on estimated settlement values; step 3 corrects that.
- **Trades can be reversed.** Kalshi may cancel or reprice trades more than 20c from fair value (Rule 5.11), and only
  your winning trades are exposed to that.
- **Sports can be blocked.** They may be unavailable through the API without location attestation.
- **Fewer fills than simulated.** Running only while the Mac is awake gives fewer fills than the 24/7 simulation.
- **Maximum loss:** the deposit. In practice it is the daily loss stop times the number of days.

## Background record (not a gate)
Keep scoring every new day with `model_b_forward.py --start 2026-10-03 --prune`, so the simulated record keeps growing
alongside the live pilot.
