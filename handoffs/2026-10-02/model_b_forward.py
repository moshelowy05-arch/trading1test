"""Model B forward test: score the frozen "standing 3c bids" fat-finger design on Kalshi's public data.

Read-only. It downloads Kalshi's public S3 daily trade reports (every trade: ticker, time to the second, size, YES
price), simulates resting orders, and values fills with OFFICIAL settlement results fetched from Kalshi's public
market endpoint (no API key). It never places an order.

Run from ~/prediction-arb (duckdb is pulled in only for this run; pyproject is not changed):
    uv run --with duckdb python handoffs/2026-10-02/model_b_forward.py --start 2026-10-03
    uv run --with duckdb python handoffs/2026-10-02/model_b_forward.py --start 2026-10-03 --prune
Re-run with --force a few days later to replace estimated marks with official results as markets settle.

Timing: day D is scored once files through D+MARK_DAYS (default 3) exist on S3 (Kalshi publishes each day about a
day later), so the newest scored day lags about four days.

RULES (the same rules the live pilot uses; see handoffs/2026-10-02/model_b_pilot_plan.md):
  - Per market, one YES bid at 3c and one NO bid at 3c (= YES ask 97c), 100 contracts each, held to settlement.
  - A side is eligible while the market's prior-600 s volume-weighted price is 20-80c with >= 3 trade-seconds; fills
    are counted only while eligible (i.e. orders are assumed cancelled when a market leaves 20-80c).
  - After a fill, that side waits 600 s before it can fill again. Combo series (KXMVE*) are excluded.
  - Fill size = min(100, max(0, beyond - C) + s * at); beyond = contracts printed strictly through 3c in that second
    (YES < 3c; for the NO side YES > 97c), at = contracts printed exactly at the level.
  - Value at settlement: the official settlement value from Kalshi when the market is determined; otherwise an
    ESTIMATE from the last trade through D+MARK_DAYS (>= 95 -> 100, <= 5 -> 0, else that price). The last-trade
    estimate is unreliable when the final second holds several prices (file order within a second is not execution
    order); on 2026-09-26 that alone moved the result by about 20%. Use official results for any decision.
Variants: base (s=0.10, C=0), through (s=0, C=0; PRIMARY: independent of queue position at 3c),
c30 / c100 (s=0, with 30 / 100 extra competitor contracts resting ahead of us).

Known limits: fills are counterfactual (the S3 file has no taker side or order book); S3 files before 2026-09-03
truncate prices to integer cents; Kalshi may cancel or reprice trades under Rule 5.11 but the S3 file keeps the
original prices; no fees are charged (the 3c makers pay none on most series; at most about 0.05c per contract).
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

import duckdb

S3 = "https://kalshi-public-docs.s3.amazonaws.com/reporting"
API = "https://api.elections.kalshi.com/trade-api/v2/markets"
ET = ZoneInfo("America/New_York")
HERE = Path(__file__).resolve().parent
CATEGORY_CSV = HERE / "series_category.csv"
VARIANTS = {"base": (0.10, 0.0), "through": (0.0, 0.0), "c30": (0.0, 30.0), "c100": (0.0, 100.0)}
LEVEL, SIZE, COOLDOWN_S = 3.0, 100.0, 600
SETTLED = {"determined", "amended", "finalized"}
SPORTS_RE = re.compile(
    r"NFL|NCAA|NBA|WNBA|MLB|NHL|MLS|EPL|UCL|UEC|UEFA|LIGA|SERIEA|BUNDES|LIGUE|SOCCER|FIFA|WC|ATP|WTA|ITF|TENNIS|UFC|"
    r"BOXING|PGA|GOLF|F1|NASCAR|INDY|CS2|LOL|VALORANT|DOTA|COD|ESPORT|CRICKET|IPL|NPB|KBO|AFL|RUGBY|DARTS|CHESS|"
    r"VOLLEY|HANDBALL|TTELITE|TABLETENNIS|AFCON|COPA|CONCACAF|FRIENDLY|GAME$|SPREAD$|TOTAL$")


def con(data: Path) -> duckdb.DuckDBPyConnection:
    c = duckdb.connect()
    (data / "tmp").mkdir(parents=True, exist_ok=True)
    c.execute(f"SET memory_limit='3GB'; SET threads=4; SET TimeZone='UTC'; SET enable_progress_bar=false; "
              f"SET temp_directory='{data / 'tmp'}'")
    return c


def ensure_day(data: Path, day: dt.date) -> bool:
    """Download and convert one ET day of trades to parquet. Returns False if Kalshi has not published it yet."""
    pq = data / "trades" / f"{day}.parquet"
    if pq.exists():
        return True
    (data / "trades").mkdir(parents=True, exist_ok=True)
    for ext in (".json.gz", ".json"):
        raw = data / f"trade_data_{day}{ext}"
        r = subprocess.run(["curl", "-sS", "-f", "-m", "1800", "-o", str(raw), f"{S3}/trade_data_{day}{ext}"],
                           capture_output=True)
        if r.returncode != 0:
            raw.unlink(missing_ok=True)
            continue
        con(data).execute(f"""COPY (SELECT ticker_name AS ticker, report_ticker AS series,
                CAST(create_ts AS TIMESTAMPTZ) AS ts, CAST(contracts_traded AS DOUBLE) AS n, CAST(price AS DOUBLE) AS p
              FROM read_json('{raw}', format='array', columns={{ticker_name:'VARCHAR', report_ticker:'VARCHAR',
                date:'VARCHAR', create_ts:'VARCHAR', contracts_traded:'VARCHAR', price:'DOUBLE'}}))
              TO '{pq}' (FORMAT parquet, COMPRESSION zstd)""")
        raw.unlink()
        print(f"  downloaded and converted {day}", flush=True)
        return True
    return False


def official_settlements(tickers: set[str], cache: Path, use_api: bool) -> dict[str, float]:
    """YES settlement value in cents for determined markets, from Kalshi's public GET /markets (cached on disk)."""
    known: dict[str, float] = json.loads(cache.read_text()) if cache.exists() else {}
    todo = sorted(t for t in tickers if t not in known)
    if use_api and todo:
        for i in range(0, len(todo), 100):
            chunk = todo[i:i + 100]
            url = f"{API}?{urllib.parse.urlencode({'tickers': ','.join(chunk), 'limit': '1000'})}"
            try:
                with urllib.request.urlopen(url, timeout=30) as r:
                    page = json.loads(r.read())
            except (urllib.error.URLError, TimeoutError) as e:
                print(f"  settlement lookup failed ({e}); unsettled values stay estimated", flush=True)
                break
            for m in page.get("markets", []):
                v = m.get("settlement_value_dollars")
                if m.get("status") in SETTLED and v not in (None, ""):
                    known[m["ticker"]] = float(v) * 100
            time.sleep(0.5)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(known))
    return known


def et_midnight_epoch(day: dt.date) -> int:
    return int(dt.datetime(day.year, day.month, day.day, tzinfo=ET).timestamp())


def score_day(data: Path, day: dt.date, categories: dict[str, str], mark_days: int, use_api: bool) -> list[dict]:
    path = lambda d: data / "trades" / f"{d}.parquet"
    flist = ",".join(f"'{path(day + dt.timedelta(k))}'" for k in (-1, 0, 1) if path(day + dt.timedelta(k)).exists())
    mlist = ",".join(f"'{path(day + dt.timedelta(k))}'" for k in range(mark_days + 1)
                     if path(day + dt.timedelta(k)).exists())
    t0, t1 = et_midnight_epoch(day), et_midnight_epoch(day + dt.timedelta(1))
    c = con(data)
    c.execute(f"""CREATE TABLE s AS SELECT ticker, any_value(series) series, epoch(ts)::BIGINT t, count(*) cnt,
          sum(n) v, sum(p*n) pv, min(p) mn, max(p) mx,
          sum(n) FILTER (WHERE p < {LEVEL}-1e-9) ylt, sum(n) FILTER (WHERE abs(p-{LEVEL})<1e-9) yat,
          sum(n) FILTER (WHERE p > {100-LEVEL}+1e-9) ngt, sum(n) FILTER (WHERE abs(p-{100-LEVEL})<1e-9) nat
        FROM read_parquet([{flist}]) WHERE epoch(ts) >= {t0 - 600} AND epoch(ts) < {t1 + 3600} GROUP BY ticker, t""")
    rows = c.execute(f"""WITH w AS (SELECT *, sum(pv) OVER b/nullif(sum(v) OVER b,0) pre600, sum(cnt) OVER b pre600_c
          FROM s WINDOW b AS (PARTITION BY ticker ORDER BY t RANGE BETWEEN 600 PRECEDING AND 1 PRECEDING)),
        lastp AS (SELECT ticker, arg_max(p, ts) last_p FROM read_parquet([{mlist}]) WHERE epoch(ts) >= {t0}
                  GROUP BY ticker)
        SELECT w.ticker, w.series, w.t, w.ylt, w.yat, w.ngt, w.nat, lastp.last_p
        FROM w JOIN lastp USING (ticker)
        WHERE w.t >= {t0} AND w.t < {t1} AND (w.mn <= 5 OR w.mx >= 95) AND w.pre600_c >= 3
          AND w.pre600 BETWEEN 20 AND 80 AND w.series NOT LIKE 'KXMVE%'
        ORDER BY w.ticker, w.t""").fetchall()
    official = official_settlements({r[0] for r in rows}, data / "settlements.json", use_api)
    out = []
    for name, (share, comp) in VARIANTS.items():
        last: dict[tuple[str, str], int] = {}
        tot = {"fills": 0, "contracts": 0.0, "pnl": 0.0, "sports": 0.0, "official": 0.0, "estimated": 0.0}
        by_event: dict[str, float] = defaultdict(float)
        for ticker, series, t, ylt, yat, ngt, nat, last_p in rows:
            if ticker in official:
                mark = official[ticker]
            else:
                mark = 100.0 if last_p >= 95 else (0.0 if last_p <= 5 else last_p)
            for side in ("yes", "no"):
                beyond = (ylt if side == "yes" else ngt) or 0.0
                at = (yat if side == "yes" else nat) or 0.0
                if beyond + at <= 0:
                    continue
                key = (ticker, side)
                if key in last and t - last[key] < COOLDOWN_S:
                    continue
                q = min(SIZE, max(0.0, beyond - comp) + share * at)
                if q <= 1e-9:
                    continue
                last[key] = t
                h = (mark - LEVEL) * q / 100 if side == "yes" else ((100 - LEVEL) - mark) * q / 100
                tot["fills"] += 1
                tot["contracts"] += q
                tot["pnl"] += h
                tot["official" if ticker in official else "estimated"] += h
                cat = categories.get(series, "")
                if cat.startswith("sports") or (not cat and SPORTS_RE.search(series.removeprefix("KX"))):
                    tot["sports"] += h
                by_event[ticker.split("-")[1] if "-" in ticker else ticker] += h
        top = sorted(by_event.values(), reverse=True)[:10]
        out.append({"date": str(day), "variant": name, "fills": tot["fills"], "contracts": round(tot["contracts"]),
                    "pnl_usd": round(tot["pnl"], 2), "pnl_official_usd": round(tot["official"], 2),
                    "pnl_estimated_usd": round(tot["estimated"], 2), "pnl_sports_usd": round(tot["sports"], 2),
                    "pnl_nonsports_usd": round(tot["pnl"] - tot["sports"], 2),
                    "top10_event_share": round(sum(top) / tot["pnl"], 3) if tot["pnl"] > 0 else "",
                    "marks_through": str(day + dt.timedelta(mark_days)),
                    "scored_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")})
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", required=True, type=dt.date.fromisoformat)
    ap.add_argument("--end", type=dt.date.fromisoformat, default=None, help="default: yesterday (ET)")
    ap.add_argument("--data-dir", type=Path, default=Path("data/s3_trades"))
    ap.add_argument("--out", type=Path, default=Path("logs/model_b_forward.csv"))
    ap.add_argument("--mark-days", type=int, default=3, help="days after D used for estimated marks (frozen: 3)")
    ap.add_argument("--force", action="store_true", help="re-score days already in the CSV (rows are appended)")
    ap.add_argument("--prune", action="store_true", help="delete trade parquet files older than the day scored")
    ap.add_argument("--no-api", action="store_true", help="skip the official-settlement lookup (estimates only)")
    a = ap.parse_args()
    end = a.end or (dt.datetime.now(ET).date() - dt.timedelta(1))
    categories: dict[str, str] = {}
    if CATEGORY_CSV.exists():
        with CATEGORY_CSV.open() as f:
            categories = {r["series"]: r["category"] for r in csv.DictReader(f)}
    done: set[tuple[str, str]] = set()
    if a.out.exists():
        with a.out.open() as f:
            done = {(r["date"], r["variant"]) for r in csv.DictReader(f)}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    day = a.start
    while day <= end:
        if not a.force and all((str(day), v) in done for v in VARIANTS):
            day += dt.timedelta(1)
            continue
        print(f"{day}: preparing", flush=True)
        if not all(ensure_day(a.data_dir, day + dt.timedelta(k)) for k in range(1, a.mark_days + 1)):
            print(f"{day}: files through D+{a.mark_days} not published yet; stopping here", flush=True)
            break
        if not (ensure_day(a.data_dir, day - dt.timedelta(1)) and ensure_day(a.data_dir, day)):
            print(f"{day}: trade file missing on S3; skipped", flush=True)
            day += dt.timedelta(1)
            continue
        rows = score_day(a.data_dir, day, categories, a.mark_days, not a.no_api)
        new = not a.out.exists()
        with a.out.open("a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            if new:
                w.writeheader()
            w.writerows(rows)
        for r in rows:
            print(f"  {r['variant']:8s} fills {r['fills']:6d}  P&L ${r['pnl_usd']:>10,.2f}  "
                  f"(official ${r['pnl_official_usd']:,.0f}, estimated ${r['pnl_estimated_usd']:,.0f}; "
                  f"sports ${r['pnl_sports_usd']:,.0f})", flush=True)
        if a.prune:
            for old in (a.data_dir / "trades").glob("*.parquet"):
                if dt.date.fromisoformat(old.stem) < day:
                    old.unlink()
        day += dt.timedelta(1)


if __name__ == "__main__":
    sys.exit(main())
