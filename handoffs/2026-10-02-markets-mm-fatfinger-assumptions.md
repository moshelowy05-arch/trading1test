# All markets, market making, fat-finger fishing, and an assumption audit — 2026-10-02

Written in a cloud session. Data comes from Kalshi's public S3 bucket (`reporting/trade_data_YYYY-MM-DD`), which has every trade on the exchange: price, size and time to the second, but no taker side and no order book. Nothing here placed an order or used an API key. Full assumption tree: [2026-10-02/assumption_tree.md](2026-10-02/assumption_tree.md). Read-only depth probe for the Mac: [2026-10-02/deep_book_probe.py](2026-10-02/deep_book_probe.py).

**What changed versus the 2026-10-01 review:**
- The 2026-10-01 review recommended a slow one-sided maker in Mentions, Entertainment and the Politics/Weather tails. That was wrong. Those categories are 0.85% of the money, paid professional market makers already work them, and the design loses on our own data.
- The one idea with a consistent positive signal is fishing with standing deep bids, called Model B below. It is a counterfactual simulation, not proven fills.

## 1. Every market (8 days, Sept 23–30, 2026)

Totals: 102.2M trades, 3,956 series, 6.94M markets, about **$478M/day** of premium and 12.8M trades/day. The totals match Kalshi's own `market_data` volume to the cent and agree with DeFi Rate.

| Category | $/day | Share | Ever examined by this project? |
|---|---|---|---|
| 15-minute crypto (BTC/ETH/SOL…) | 141.5M | 29.6% | No (only the taker hard-arb sweep) |
| Tennis (Challenger/ITF about $55M) | 77.4M | 16.2% | Lower tiers never |
| US football (NFL, NCAAF) | 71.1M | 14.9% | Yes, cross-venue taker arbitrage only |
| Combos / parlays | 66.6M | 13.9% | Never (excluded from sweeps) |
| Baseball | 34.8M | 7.3% | MLB taker arbitrage only |
| Soccer | 22.5M | 4.7% | Mostly never |
| 15-minute commodities/FX | 19.3M | 4.0% | Never |
| Crypto hourly ladders | 18.4M | 3.8% | KXETHD ladders |
| Everything else (politics, weather, mentions, entertainment, economics, esports…) | about 27M | about 5.6% | Desk reviews only |

- **Concentration.** The top 10 series hold 66.7% of premium and the top 50 hold 90.8%. 2,820 series trade under $1k/day.
- **Coverage.** The project's own measurements covered about 20% of premium, and only for taker arbitrage. Nothing was ever tested for market making or fat-finger fishing.
- **Maker fees.** About 55% of premium trades in series where makers pay nothing. 19% is in series that charge makers 0.25× the taker fee, 12% is combos at 0.5×, and 13% is unknown.
- **Contract rules.** Fractional contracts (minimum 0.01) are universal. Sub-cent ticks are almost entirely in combos and in the <10c / >90c bands of 15-minute markets.

## 2. Market making (two-sided quoting)

**Verdict: not a retail edge.** An independent checker confirmed this and found it stronger than first measured. The binding constraint is adverse selection: a slow quoter is filled mainly when informed or fast flow runs through its quote.

**Sign-free simulation of a slow quote** (re-centred every 10–300 s, fills only on trade-through), loss per contract by family:

| Family | Loss per contract |
|---|---|
| Daily-high temperature | about 1c |
| Mentions and hourly temperature | 3–6c |
| Crypto hourly | 1.5–4.5c |
| 15-minute crypto | 1–3c |
| State gas, near the touch | 9–15c |

- **Break-even families.** Rain is about zero. NFL is about zero after its 0.276c maker fee, and NFL is a sports contract.
- **Liquidity Incentive Program, rain:** refuted. Fills cost $1.3–3.2k/day against at most $0.3–0.7k/day of reward.
- **Liquidity Incentive Program, state gas:** the only open case. It is positive only if a single third-party snapshot of reward share holds. Incumbents can add size at will, and the program ends by 2027-01-01.
- **Structural advantages belong to designated market makers.** They get fee benefits, 10× position limits, Rule 5.11(d) error relief, an in-game sports data feed (from 2026-09-22) and the MM-only Liquidity Provider Program, which pays up to $50k/week per series in Weather, Mentions, Crypto and more.
- **Infrastructure:** API keys are self-serve and a demo environment exists, but demo fills say nothing about real economics.

## 3. Fat-finger fishing

**Taking every extreme print loses money.** Buying at 1–5c or 95–99c whenever a market prints there returned −7.3% (an independent recheck got −7.6%). 96–98% of those fills are real moves, not errors.

**Model B is positive in every window tested.** Model B rests one 3c YES bid and one 3c NO bid of 100 contracts in every non-combo market that traded 20–80c over the prior 10 minutes, refills at most every 10 minutes, and holds to settlement. It is a **counterfactual**: it assumes our order was resting when the trade happened. It counts a fill only from volume that traded beyond 3c, or from 10% of volume at exactly 3c. Price priority means existing queue position cannot block a fill that traded through our price.

| Window | $/day (no extra competition) | 30 extra contracts ahead of us | 100 extra contracts ahead of us | Days positive | Source |
|---|---|---|---|---|---|
| Jul 14–21, 2025 (before the volume rebate program) | 283 | — | 227 | 7/8 | attack-evidence agent |
| Oct 13–19, 2025 | 729 | 555 | 388 | 7/7 | this session (r3/season_test.py) |
| Mar 16–22, 2026 (March Madness) | 1,835 | 874 | 461 | 7/7 | this session |
| Jul 13–19, 2026 (summer, World Cup, no football) | 3,619 | 1,890 | 763 | 7/7 | this session |
| Aug 10–17, 2026 | 2,693 | 2,104 | 1,378 | 8/8 | assumption-tree agent |
| Sep 10–15, 2026 | 2,955 | 2,005 | 831 | 6/6 | verifier |
| Sep 16–22, 2026 (never used to design the rule) | 2,905 | 1,663 | 460 | 7/7 | attack-missing agent |
| Sep 23–30, 2026 (design window) | 1,989 | 775 | −281 | 8/8 | verifier (reproduced exactly here) |
| Oct 1, 2026 | 2,426 | — | 1,047 | 1/1 | attack-evidence agent |

**How to read the table**
- Model B was positive on 58 of 59 test days with no extra competition.
- The competition columns come from two slightly different engines. Mine applies the extra competitor size to through-volume only.
- S3 files before 2026-09-03 store prices truncated to integer cents, so older windows carry a small bias.
- Profit at a fixed size grew with Kalshi's volume, but profit per $1M traded fell about 6× in a year.

**What the profit actually is**
- In September, most of the profit came from about 120 fills/day in markets that were mid-range just before the crash and snapped back within 60 seconds.
- Another large part comes from live-game lines (often basketball totals or spreads) that crash to 1–3c, stay low for 10+ minutes, and then win anyway.
- About 80% of fills are stale "lottery tickets" that net roughly zero.
- P&L is lumpy: the top 50 events carry 73–91% of a window's profit.
- Sports were 34–73% of P&L depending on the window. Combos lose and are excluded.

**What could still kill it.** None of these can be settled from the trade tape alone.
1. **Real fills.** The tape has no taker side and no order book. Only real orders, or full-depth books plus taker side, can confirm the fill model.
2. **Competition.** With 100–300 contracts resting ahead of ours, the edge goes to zero or negative. Depth at 3c showed no build-up through Oct 1. In sub-cent markets a rival can jump ahead for 0.1c.
3. **An always-on canceller.** The simulation cancels the moment a market leaves 20–80c. Without that (a sleeping Mac), P&L with 30 contracts ahead falls 15–32%, and with 100 ahead it turns negative in 2 of 3 windows. The fix is orders with expiry times plus amending the expiry, which keeps queue priority; it still needs an always-on machine, for example a small cloud server. Kalshi's member agreement makes members responsible for their own servers and does not forbid them.
4. **API geofencing.** Since 2026-08-16, API keys carry a location attestation that expires. After that, keys cannot trade Sports, Elections or Entertainment. That is 36–68% of Model B P&L. NJ is currently lawful (Third Circuit), but how the attestation renews is unknown.
5. **Rule 5.11 is asymmetric.** Only the harmed side asks for a review, so only Model B's winning fills can be cancelled or repriced (the July 2025 MLB precedent repriced 99c prints). Most events are too small for the requester to pay the $3,000 fee, and Kalshi also acts on its own initiative.
6. **Tax** (computed here on the simulated fills):
   - Capital-gains treatment: about 30% off.
   - Gambling treatment, itemizing: taxable income is 1.2–1.3× true profit.
   - Gambling treatment, not itemizing: taxable is 3–4× profit, and in-sample after-tax turns **negative**.
   - A CPA opinion is required.
7. **Regime.** The Volume Incentive Program ends 2026-10-13. Klear margin for professionals arrives around 2026-11-09. Settlement is discretionary under Rules 7.1 and 7.2.

**Other assumption checks done in this session**
- Pause and reopen order wipes explain only about $250 of $15.9k of profit. Most profit comes during continuous trading.
- The settlement proxy (last trade) matched truth in 7,073/7,077 crypto markets and 290/290 weather brackets.
- Twelve primary-source facts the agents relied on were checked against the documents, and all twelve matched. Some secondary items were wrong or disputed:
  - the Polymarket US rebate start date;
  - Kalshi's Nov-9 Supreme Court response extension;
  - the APY (3.50, 3.75 or 4.05%).

## 4. What the assumption audit overturned

The audit found 135 assumptions plus 26 missing ones. After two attack passes: 32 contradicted, 21 unverified, 25 verified on data, 13 verified from primary documents, 31 secondary, 13 judgment. 43 would flip a conclusion.

Contradicted and load-bearing:
- "No API keys" is a hard constraint. **False:** keys are self-serve, with read-only scopes and a demo environment.
- REST polling and the taker-first framing were the right way to search. **False:** they were the main blind spot. Most of the exchange was never looked at with maker or deep-order strategies.
- Slow non-sports niches lack professionals. **False:** the Liquidity Provider Program pays MM firms in exactly those categories.
- Slow one-sided maker in Mentions/Entertainment/Politics is the best candidate. **False:** it loses on our tape on through-fills, except Weather <10c at about $100/day.
- Competition is static. **False:** in-game data feed for top makers, Klear margin, settlement-floor order cancels, new reward programs.
- Combos have no book, so hard arbitrage there is impossible. **False:** combos have public books, so 13.9% of premium was never checked for arbitrage.
- Non-sports is legally safe. **False in general:** Washington's injunction also covers politics, mentions and entertainment, and other states geofence. NJ is fine for now.
- The TSA backup is better than the alternatives. **False:** that market trades about $373/day.

Still unverified and load-bearing (Mac-only checks):
- Study 1's fee model handles 2026 fee changes: centicent rounding from 2026-05-28, per-series multipliers, the 2026-07-03 index change, combo maker fees from 2026-08-20.
- Study 1 prices are exact in sub-cent markets.
- pmarb's own fee engine and queue model are correct.
- Combo parlay bounds hold.

New candidates the audit surfaced:
- **Taker NO-favourites by category.** In Politics, Entertainment, Economics and Sci-Tech, takers buying NO at 90–100c gained +1.2 to +3.2c gross in both halves of Dec-2025..Sep-2026 (third-party data with true taker side). The cells were picked after the fact, so this needs pre-registration.
- **ForecastEx.** Unexamined, not refuted.

## 5. Recommendation

1. **Keep Study 1 running exactly as pre-registered.** Before unsealing, verify its fee model and its sub-cent price handling on the Mac.
2. **Make Model B "Study 2".** Freeze its rules now: 3c both sides, 100 contracts, 10-minute refill, 20–80c eligibility, combos excluded, cancel when a market leaves the band. Forward-score it on every new S3 day, especially after 2026-10-13. This runs in the cloud with no keys, no Mac and no money.
3. **Measure competition from the Mac,** keyless and read-only: `uv run python handoffs/2026-10-02/deep_book_probe.py`, run once now and weekly. Also pull true taker side (`GET /markets/trades`) and settled results for the fill study.
4. **Decisions only Moshe can make** (nothing proceeds without them):
   - create API keys (self-serve; start read-only);
   - whether to rent an always-on server (a few dollars a month), since the Mac sleeps;
   - get a CPA opinion on tax treatment;
   - later, whether to run a **tiny live probe**: 1-contract 3c orders, worst case 3c per fill, a few tens of dollars at risk. It is the only way to measure real fills, queue position and Rule 5.11 behaviour. It requires the project's live-trading guard to be deliberately enabled, and it is not authorised by anything in this document.
5. **Drop or demote:**
   - two-sided market making;
   - the slow non-sports maker (the 2026-10-01 primary);
   - the TSA nowcast;
   - catching every extreme print.

## 6. Honest expectation

**The case for Model B**
- It is the first idea in the project with a consistent positive signal in real data across nine separate windows spanning a year.
- It needs little capital: about $3–9k resting.

**The case against**
- It is a simulation of orders that were never placed.
- It is easy for others to copy, and competition of a few hundred contracts erases it.
- It needs always-on automation and API keys that may be blocked from sports.
- Its winning trades are the ones Kalshi can reverse.
- Tax can erase it for a non-itemizer.

**Range of outcomes**
- From about zero, if real fills or competition disappoint, to roughly $1–3k/day before tax, if the trade-tape counterfactual holds and sports stay accessible.
- A realistic central case after frictions is well below the headline numbers.
- The cheap forward test and the depth probe should narrow this within two to four weeks, before any money is at risk.
