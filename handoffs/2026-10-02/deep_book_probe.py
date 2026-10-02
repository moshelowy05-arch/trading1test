"""Read-only snapshot of resting depth at extreme prices on Kalshi (public endpoints, no API key, no orders).

Why: the fat-finger "standing 3c bid" result is a counterfactual from the public trade tape. Its main risk is
competition, i.e. how much size already rests at 1-5c (YES bids) and 95-99c (= NO bids at 1-5c) in markets
trading 20-80c. Run this once now and again weekly; growing deep depth is a kill signal.

Usage (from ~/prediction-arb):   uv run python handoffs/2026-10-02/deep_book_probe.py [--max-markets 3000]
Writes logs/deep_book_<UTC timestamp>.json and prints a summary. Gentle: about 2 requests/second.
Endpoints (docs mirror github.com/ammario/kalshi-docs): GET /markets (status=open, mve_filter=exclude, limit<=1000),
GET /markets/orderbooks (tickers, max 100 per call; returns YES bids and NO bids only, [price_dollars, contracts]).
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://api.elections.kalshi.com/trade-api/v2"
PAUSE_S = 0.5


def get(path: str, params: list[tuple[str, str]]) -> dict:
    url = f"{BASE}{path}?{urllib.parse.urlencode(params)}"
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"Accept": "application/json"}), timeout=30) as r:
                time.sleep(PAUSE_S)
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2 ** attempt)
                continue
            raise
    raise RuntimeError(f"rate limited repeatedly: {path}")


def dollars(x: str | None) -> float | None:
    return None if x in (None, "") else float(x)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-markets", type=int, default=3000, help="cap on mid-range markets to snapshot")
    args = ap.parse_args()

    mids: list[dict] = []
    cursor = ""
    pages = 0
    while True:
        params = [("status", "open"), ("mve_filter", "exclude"), ("limit", "1000")]
        if cursor:
            params.append(("cursor", cursor))
        page = get("/markets", params)
        pages += 1
        for m in page.get("markets", []):
            bid, ask = dollars(m.get("yes_bid_dollars")), dollars(m.get("yes_ask_dollars"))
            if bid is None or ask is None or bid <= 0 or ask >= 1:
                continue
            mid = (bid + ask) / 2
            if 0.20 <= mid <= 0.80:
                mids.append({"ticker": m["ticker"], "series": m["ticker"].split("-")[0], "mid": mid, "spread": ask - bid})
        cursor = page.get("cursor") or ""
        if not cursor:
            break
    print(f"listed {pages} pages; {len(mids)} open non-combo markets with a two-sided quote and mid 20-80c")
    mids = mids[: args.max_markets]

    books: dict[str, dict] = {}
    for i in range(0, len(mids), 100):
        chunk = [m["ticker"] for m in mids[i : i + 100]]
        try:
            resp = get("/markets/orderbooks", [("tickers", t) for t in chunk])
            for ob in resp.get("orderbooks", []):
                books[ob["ticker"]] = ob.get("orderbook_fp", {})
        except urllib.error.HTTPError as e:
            if e.code != 401:
                raise
            for t in chunk:  # batch endpoint needs auth on this account: fall back to the single-market endpoint
                books[t] = get(f"/markets/{t}/orderbook", [("depth", "100")]).get("orderbook_fp", {})

    levels = [0.01, 0.02, 0.03, 0.04, 0.05]
    per_series: dict[str, list] = defaultdict(list)
    rows = []
    for m in mids:
        ob = books.get(m["ticker"])
        if ob is None:
            continue
        yes = {round(float(p), 4): float(q) for p, q in ob.get("yes_dollars") or []}
        no = {round(float(p), 4): float(q) for p, q in ob.get("no_dollars") or []}
        row = {**m,
               "yes_bid_1_5c": {f"{int(L*100)}c": yes.get(L, 0.0) for L in levels},
               "no_bid_1_5c": {f"{int(L*100)}c": no.get(L, 0.0) for L in levels},
               "yes_bid_subcent_below_5c": sum(q for p, q in yes.items() if p < 0.05 and round(p * 100, 6) != int(p * 100)),
               "no_bid_subcent_below_5c": sum(q for p, q in no.items() if p < 0.05 and round(p * 100, 6) != int(p * 100))}
        rows.append(row)
        per_series[m["series"]].append(row)

    def share_zero(key: str, upto: float) -> float:
        z = [r for r in rows if sum(v for k, v in r[key].items() if int(k[:-1]) <= upto * 100) == 0]
        return round(len(z) / len(rows), 3) if rows else float("nan")

    def median(xs: list[float]) -> float:
        xs = sorted(xs)
        return xs[len(xs) // 2] if xs else float("nan")

    summary = {
        "snapshot_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "markets": len(rows),
        "share_with_no_yes_bid_at_1to3c": share_zero("yes_bid_1_5c", 0.03),
        "share_with_no_no_bid_at_1to3c": share_zero("no_bid_1_5c", 0.03),
        "median_yes_bid_size_at_3c": median([r["yes_bid_1_5c"]["3c"] for r in rows]),
        "median_yes_bid_size_2to5c": median([sum(r["yes_bid_1_5c"][k] for k in ("2c", "3c", "4c", "5c")) for r in rows]),
        "median_no_bid_size_2to5c": median([sum(r["no_bid_1_5c"][k] for k in ("2c", "3c", "4c", "5c")) for r in rows]),
        "median_spread_cents": round(median([r["spread"] for r in rows]) * 100, 2),
        "top_series_by_markets": sorted(
            ({"series": s, "markets": len(v),
              "median_yes_2to5c": median([sum(r["yes_bid_1_5c"][k] for k in ("2c", "3c", "4c", "5c")) for r in v]),
              "median_no_2to5c": median([sum(r["no_bid_1_5c"][k] for k in ("2c", "3c", "4c", "5c")) for r in v])}
             for s, v in per_series.items()), key=lambda d: -d["markets"])[:40],
    }
    out = Path("logs") / f"deep_book_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"summary": summary, "markets": rows}, indent=1))
    print(json.dumps(summary, indent=1))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
