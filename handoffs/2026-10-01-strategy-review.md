# Strategy review and wrap-up — 2026-10-01

Written in a cloud session that cannot reach the Mac. Copy it to `~/prediction-arb/handoffs/` if you want it there.
Every number in sections 3–5 comes from public sources, cited at the end. None was measured on our own data.

## 1. What has been done

| Phase | What we tested | Result |
|---|---|---|
| A. Cross-venue sports arbitrage, Kalshi ↔ Polymarket US | 7,432 fresh samples, replay, paper/shadow | One net-positive instant worth $0.03. Paper/shadow: one fill with a failed hedge, −$1.12. **Dead.** |
| B. Kalshi ladder arbitrage | 873,640 nested checks; 4,722 partition states | 0 gross-positive; 0 net-positive. **Dead.** |
| Step 2: every provable hard-arbitrage family | 7 sweeps of the whole universe (~12.7k events, 121k markets each) | 491 live-confirmed candidates; **0 survived fees** (all one-tick overrounds). |
| Within-game relationships | about 480k checks | 3 samples at +0.06¢ to +0.5¢. Negligible. |
| Study 1: calibration and the "tails" rule (pre-registered) | Apr–Aug 2026, 57,069 markets | **Running.** Candles 19,600/152,984 at last check; prints not started; nothing frozen or unsealed. |

Conclusion so far: taker arbitrage on public Kalshi data is exhausted. Live trading stays disabled.

## 2. The pasted memo: what holds and what doesn't

Its conclusion holds: don't trade a taker tails rule with real money. Many of its specifics are wrong or outdated.

| Claim | Verdict |
|---|---|
| Kalshi ended its Volume Incentive Program effective Oct 13, 2026 | **True.** Primary CFTC filing dated Sep 28, 2026; the original end date was Oct 1, 2027. The filing gives no reason. The snapshot-scoring rules the memo describes belong to the separate *Liquidity* Incentive Program, which runs until Jan 1, 2027. |
| Taker fee = round-up(0.07·C·P·(1−P)) to the cent | **Outdated.** Since May 28, 2026, kalshi.com accounts round up to $0.0001, not $0.01; for a 1-lot at 97¢ that is 0.21¢, not 1¢. There is also a per-series multiplier. Makers pay **0** on ~14,200 series, including weather, crypto and mentions. About 160 series charge makers 0.25× the taker fee: major sports, Fed, CPI, GDP and awards. |
| "$25k retail position limit" | **Mischaracterized.** It is a soft accountability level of $25k max loss per strike, per member, for everyone. It does not bind at our size. |
| Returns-by-price table (−40%, −16.3%, +1.7%, +3.1%) | **False.** It is not the Bürgi/Deng/Whelan table. +3.1% is an illustrative example from the paper's text, −16.3% comes from a different dataset, and the 95–99¢ row is internally inconsistent: a 97% price winning 98% returns +1.0%. |
| "4,904 bots, 2.1% survived" | **Mischaracterized.** It is a vendor's (TurbineFi) backtest of 4,904 parameter variants on one 15-minute BTC series, not real bots. |
| "Brier 0.09 vs sportsbooks 0.18–0.22" | **Misleading comparison.** On the same games, Kalshi and sportsbooks score the same. |
| Domain/horizon calibration paper (292M trades) | **Real** (arXiv 2602.19520, v1 numbers). Its long-horizon effect does not survive a quote-based, event-clustered re-test. |
| "10–40¢ contracts in the last 10 minutes almost never win"; "crashing favorites cost 8¢/fill" | **No source found.** Treat as invented. |
| Tax ambiguity | **Largely true.** No IRS guidance on event contracts. Since 2026, only 90% of gambling losses are deductible. Kalshi issues no comprehensive 1099-B for event contracts. **Get a CPA opinion before any real money.** |
| (Not in memo) Interest | Kalshi pays variable interest on cash **and open positions**: about 3.5–3.75% APY, exact rate unverified. That weakens the memo's "capital lock-up" argument. It also sets the baseline any strategy must beat. |
| (Not in memo) New Jersey | Kalshi is currently lawful in NJ (Third Circuit, Apr 6, 2026). NJ has petitioned the Supreme Court (No. 26-299). Two other circuits have ruled against Kalshi. The risk is to **sports** contracts in 2027; non-sports contracts are not at issue. |

## 3. Calculations: the tails strategy (Study 1's subject)

**Sources.** Fees use today's formula, rounded to $0.0001. Edge comes from an independent replication of Bürgi/Deng/Whelan on 2021–Apr 2025 data. The paper's own PDF was blocked here, so its exact band values are unverified.

**Columns.**
- "Taker, realistic" = the taker's share of the edge (makers capture most of it).
- "Maker" = an upper bound on fee-free series. Professional makers earned it, not a slow retail one.

| Buy the favorite at | Taker fee / contract | Taker, realistic, per position | Maker (fee-free series), per position |
|---|---|---|---|
| 50¢ (reference) | 1.75¢ | −3.4% | 0% |
| 85¢ | 0.89¢ | −0.5% | +2.2% to +3.5% |
| 90¢ | 0.63¢ | −0.3% | +1.8% to +2.9% |
| 95¢ | 0.34¢ | −0.1% | +1.2% to +1.9% |
| 97¢ | 0.21¢ | 0.0% | +0.8% to +1.3% |

- **A taker makes about zero.** If the bias has faded since the paper was published (the evidence can't tell yet), a taker loses exactly the fee.
- **Only the maker side shows a positive return**, and it needs API keys to place orders.
- **Capacity:** about $0.5k–$5.6k/day of entries without moving prices. The best realistic case is about $6k/yr whatever the account size.
- **Tail risk:** at 95¢, one loss wipes out about 20 wins.
- **Tax:** under worst-case gambling treatment, taxable income can be 1.3–1.8× true income at 90–97¢.

**Decision:** keep Study 1 running exactly as pre-registered, as a measurement. Do **not** trade its rule even on a marginal pass.

## 4. New strategy candidates (12 generated, 4 deep-dived, then red-teamed)

### Primary (research only): slow passive maker in fee-free, non-sports categories
- **What it is.** Post resting orders that bet *against* hyped YES outcomes and wait for impatient buyers. Fills come at the back of the queue, in 10-lots, held to settlement.
- **Categories.** Mentions, Entertainment, and the longshot tails of Politics and Weather.
- **Why it might work.**
  - Three independent datasets show makers beat takers on Kalshi, by the most in media and entertainment.
  - A pre-registered third-party backtest (`paandrighetti/kalshi-maker`) found 7 of 289 cells positive in both test periods, all betting against YES.
  - Makers pay no fees on these series.
  - Non-sports, so outside the NJ dispute.
- **Why it might not.**
  - Nobody has measured how many fills a slow retail maker actually gets, or how adversely selected they are.
  - The most conservative statistic is significant in 4 of the 6 cells, but not in the largest one (Mentions 30–70¢, t 1.47).
  - The premium is published.
  - Volume incentives end Oct 13.
- **Money if it works:** about $2–9k/yr pre-tax on $25k, limited by capacity. Pessimistic case: −$2.5k/yr.
- **Odds** (judgment calls by the reviewing agents, not measured):
  - about 50% it passes a backward sealed test;
  - about 10% that the whole chain works (backward test, then forward paper test, then live trading once API keys exist).

### Backup: TSA weekly check-in markets (KXTSAW) vs a public nowcast
- **The idea.** TSA publishes daily counts each morning, so the weekly average becomes predictable before the market closes.
- **Evidence.** The nowcast carries information beyond price in 2026: +$72/week, t 2.5.
- **Weaknesses.** The 2025 out-of-sample year fails once you pay a 3¢ spread. The whole market trades only about $4.9k/week.
- **Value.** A ceiling of about $1–3k/yr: a cheap validation, not an income.

### Dropped
| Idea | Why it was dropped |
|---|---|
| Weather vs forecast models | The only positive backtest has a look-ahead flaw. Independent pre-registered tests found no edge (`anaborne/kalshi-temperature-calibration`). Only option kept: start recording KXHIGH evening books from Nov 1. |
| Long-horizon underconfidence | Measured slope ≈ 1.07 with no growth over horizon; the taker version lost 3.1¢ at T−7d. |
| Crypto ladders vs options | Crowded, institutional. |
| Index ladders vs options | Built on an outdated premise: the half-fee ended Jul 3. |
| Macro nowcasts | About 12 events a year leaves too little data to test. |
| Fed vs futures | Efficient. |
| ForecastEx maker | Needs an IBKR account; eligibility unverified. |
| NBA in-play | Sports, NJ legal risk, and a latency race. |
| Midterm races | One correlated cluster, no statistical power. |

## 5. Next steps (none trade; none need API keys)
1. **Let Study 1 finish.** At Checkpoint 2, approve only the pre-registered rule.
   - Before unsealing, check that Study 1's fee model handles:
     - rounding to $0.0001 from May 28, 2026;
     - per-series multipliers (MLB 0.5× pre-game);
     - the Jul 3 index-fee change;
     - the Aug 20 combo maker fees.
   - This could not be checked from the cloud copy.
2. **Maker study, backward test.** Pre-register first, then run a sealed test on May–Nov 2025 public trades with taker side, about 2–3 days of code.
   - Kill if:
     - the conservative edge is ≤ +0.5¢;
     - or t < 2.28;
     - or both headline cells are ≤ 0;
     - or more than 50% of the P&L comes from 5% or fewer of events.
3. **Maker study, 10-day shadow test.** Record about 100 open, fee-free Mentions/Entertainment markets and run the paper maker.
   - Kill if:
     - fills are under 300 contracts/day;
     - or the 10-minute markout is worse than −2¢ per contract.
4. **If both pass:** a 90–180-day forward paper test plus a CPA tax opinion. Only after that: API keys, LiveGuard, and a decision about money.
5. **Backup:** the TSA study, about 4–6 days, run after Study 1.

Overall expectation: about 15–20% that anything here yields ≥ $1k/yr after tax and costs by end-2027, and about 80% that it ends in another well-documented null.

## Suggested PROXIMO.md "Current state" addition
> 2026-10-01 strategy review (handoffs/2026-10-01-strategy-review.md): the taker tails rule is not tradable (≈0 after fees);
> Study 1 continues as a measurement only. Next research candidate: slow passive maker on fee-free non-sports series
> (Mentions/Entertainment/Politics- and Weather-tails), backward sealed test first; backup: KXTSAW nowcast.

## Sources
- Bürgi, Deng & Whelan, *Makers and Takers* — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5502658 ; summary https://cepr.org/voxeu/columns/economics-kalshi-prediction-market
- Replication / persistence test — https://github.com/Vladosyna/kalshi-makers-takers-persistence
- Slow-maker pre-registered backtest — https://github.com/paandrighetti/kalshi-maker (reports/BACKTEST.md)
- Event-clustered calibration — https://github.com/nalimmm/kalshi-calibration
- Weather pre-registered null — https://github.com/anaborne/kalshi-temperature-calibration ; isobar — https://github.com/abelianbee/isobar
- Domain calibration paper — https://arxiv.org/abs/2602.19520
- VIP termination — https://kalshi-public-docs.s3.amazonaws.com/regulatory/notices/Termination%20of%20Volume%20Incentive%20Program.pdf ; https://cryptobriefing.com/kalshi-ends-volume-incentive-program/
- Fee rounding / fee types (docs mirror) — https://github.com/ammario/kalshi-docs/blob/main/getting_started/fee_rounding.md ; https://github.com/ammario/kalshi-docs/blob/main/changelog.md
- Rulebook v1.29 (position accountability) — https://kalshi-public-docs.s3.amazonaws.com/regulatory/rulebook/Kalshi%20DCM%20Rulebook%20v.1.29.pdf
- Interest — https://help.kalshi.com/en/articles/13823847-apy-on-kalshi
- TSA contract terms — https://kalshi-public-docs.s3.amazonaws.com/contract_terms/TSAW.pdf
- Bot "study" — https://www.turbinefi.com/blog/5000-strategy-backtest-kalshi-btc-15m
- NJ: Third Circuit — https://law.justia.com/cases/federal/appellate-courts/ca3/25-1922/25-1922-2026-04-06.html ; cert petition — https://www.supremecourt.gov/docket/docketfiles/html/public/26-299.html
- Gambling-loss 90% cap — https://www.foster.com/larry-s-tax-law/one-big-beautiful-bill-act-part-3-gambling-code-section-165-d
