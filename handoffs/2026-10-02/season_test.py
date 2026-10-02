"""Independent seasonality / persistence test of fat-finger 'Model B' (standing 3c bids both sides).
NOTE: copied from the cloud session scratchpad; paths (R, CAT) point there. Logic matches verify-ff/f_sim.py (reproduced its 1,989 USD/day in-sample result exactly).
Re-implements the verifier's extraction + simulation (verify-ff/f_extract_oos.py, f_sim.py) for arbitrary periods.
Usage: python3 season_test.py <label> <first_day> <n_days>   (downloads n_days + 1 extra day for marks)
"""
import sys, os, json, time, collections, subprocess, datetime as dt
import duckdb
R = "/tmp/claude-0/-home-user-trading1test/7b77102f-3f54-52b9-947e-301b6018578a/scratchpad/r3"
CAT = "/tmp/claude-0/-home-user-trading1test/7b77102f-3f54-52b9-947e-301b6018578a/scratchpad/r2/census/series_category.csv"
label, first, nd = sys.argv[1], dt.date.fromisoformat(sys.argv[2]), int(sys.argv[3])
D = f"{R}/{label}"; os.makedirs(f"{D}/raw", exist_ok=True); os.makedirs(f"{D}/trades", exist_ok=True); os.makedirs(f"{D}/tmp", exist_ok=True)
days = [first + dt.timedelta(d) for d in range(-1, nd + 1)]   # one day before (references) and after (marks)
for d in days:
    pq = f"{D}/trades/{d}.parquet"
    if os.path.exists(pq): continue
    for ext in (".json.gz", ".json"):
        f = f"{D}/raw/trade_data_{d}{ext}"
        if not os.path.exists(f):
            r = subprocess.run(["curl", "-sS", "-f", "-m", "900", "-o", f, f"https://kalshi-public-docs.s3.amazonaws.com/reporting/trade_data_{d}{ext}"])
            if r.returncode != 0:
                if os.path.exists(f): os.remove(f)
                continue
        con = duckdb.connect(); con.execute(f"SET memory_limit='3GB'; SET threads=4; SET TimeZone='UTC'; SET temp_directory='{D}/tmp'")
        con.execute(f"""COPY (SELECT CAST('{d}' AS DATE) AS day, ticker_name AS ticker, report_ticker AS series,
              CAST(create_ts AS TIMESTAMPTZ) AS ts, CAST(contracts_traded AS DOUBLE) AS n, CAST(price AS DOUBLE) AS p
            FROM read_json('{f}', format='array', columns={{ticker_name:'VARCHAR', report_ticker:'VARCHAR', date:'VARCHAR', create_ts:'VARCHAR', contracts_traded:'VARCHAR', price:'DOUBLE'}}))
            TO '{pq}' (FORMAT parquet, COMPRESSION zstd)""")
        os.remove(f); print("converted", d, flush=True); break
    else:
        print("MISSING", d, flush=True)
P = f"{D}/trades/*.parquet"
con = duckdb.connect(); con.execute(f"SET memory_limit='3GB'; SET threads=4; SET TimeZone='UTC'; SET enable_progress_bar=false; SET temp_directory='{D}/tmp'")
print(label, "trades/day:", con.execute(f"SELECT day, count(*), round(sum(n*p)/100/1e6,1) FROM read_parquet('{P}') GROUP BY 1 ORDER BY 1").fetchall(), flush=True)
con.execute(f"CREATE TABLE lastp AS SELECT ticker, arg_max(p, ts) last_p FROM read_parquet('{P}') GROUP BY ticker")
lv = ",".join([f"sum(n) FILTER (WHERE p < {L}-1e-9) ylt{L}, sum(n) FILTER (WHERE abs(p-{L})<1e-9) yat{L}, sum(n) FILTER (WHERE p > {100-L}+1e-9) ngt{L}, sum(n) FILTER (WHERE abs(p-{100-L})<1e-9) nat{L}" for L in (1, 2, 3, 5)])
fxs = []
for d in days[1:-1]:
    out = f"{D}/fx_{d}.parquet"; fxs.append(out)
    if os.path.exists(out): continue
    t0 = time.time(); d0 = f"TIMESTAMPTZ '{d} 04:00:00+00'"
    c2 = duckdb.connect(); c2.execute(f"SET memory_limit='3GB'; SET threads=4; SET TimeZone='UTC'; SET enable_progress_bar=false; SET temp_directory='{D}/tmp'")
    c2.execute(f"""CREATE TABLE s AS SELECT ticker, any_value(series) series, epoch(ts)::BIGINT t, CAST(timezone('America/New_York', min(ts)) AS DATE) dday, count(*) c, sum(n) v, sum(p*n) pv, min(p) mn, max(p) mx, {lv}
      FROM read_parquet('{P}') WHERE ts >= {d0} - INTERVAL 600 SECOND AND ts < {d0} + INTERVAL 1 DAY + INTERVAL 3600 SECOND GROUP BY ticker, t""")
    c2.execute(f"""COPY (WITH w AS (SELECT *,
        sum(pv) OVER b10/nullif(sum(v) OVER b10,0) pre600, sum(c) OVER b10 pre600_c,
        sum(pv) OVER b2/nullif(sum(v) OVER b2,0) pre120, sum(c) OVER b2 pre120_c,
        sum(pv) OVER a1/nullif(sum(v) OVER a1,0) post60, sum(c) OVER a1 post60_c,
        sum(pv) OVER a10/nullif(sum(v) OVER a10,0) post600, sum(c) OVER a10 post600_c,
        sum(pv) OVER al/nullif(sum(v) OVER al,0) post3600, sum(c) OVER al post3600_c,
        lag(pv) OVER o/nullif(lag(v) OVER o,0) prev_vwap
      FROM s WINDOW b10 AS (PARTITION BY ticker ORDER BY t RANGE BETWEEN 600 PRECEDING AND 1 PRECEDING),
                    b2 AS (PARTITION BY ticker ORDER BY t RANGE BETWEEN 120 PRECEDING AND 1 PRECEDING),
                    a1 AS (PARTITION BY ticker ORDER BY t RANGE BETWEEN 1 FOLLOWING AND 60 FOLLOWING),
                    a10 AS (PARTITION BY ticker ORDER BY t RANGE BETWEEN 1 FOLLOWING AND 600 FOLLOWING),
                    al AS (PARTITION BY ticker ORDER BY t RANGE BETWEEN 601 FOLLOWING AND 3600 FOLLOWING),
                    o AS (PARTITION BY ticker ORDER BY t))
      SELECT * EXCLUDE (pv) FROM w WHERE dday = DATE '{d}' AND (mn <= 5 OR mx >= 95) AND pre600_c >= 1) TO '{out}' (FORMAT PARQUET)""")
    print("extracted", d, f"{time.time()-t0:.0f}s", flush=True)
con.execute(f"COPY lastp TO '{D}/lastp.parquet' (FORMAT PARQUET)")
cols = ["ticker","series","t","dday","pre600","pre600_c","pre120","pre120_c","prev_vwap","post60","post60_c","post600","post600_c","post3600","post3600_c","last_p","category"] + \
       [f"{k}{L}" for L in (1, 2, 3, 5) for k in ("ylt","yat","ngt","nat")]
fxl = ",".join(f"'{x}'" for x in fxs)
rows = con.execute(f"""SELECT {','.join('f.'+c if c not in ('last_p','category') else c for c in cols)}
  FROM read_parquet([{fxl}]) f LEFT JOIN '{D}/lastp.parquet' l USING (ticker) LEFT JOIN (SELECT series, category FROM read_csv_auto('{CAT}')) c USING (series)
  WHERE f.pre600_c >= 3 AND f.pre600 BETWEEN 20 AND 80 AND f.series NOT LIKE 'KXMVE%' ORDER BY f.ticker, f.t""").fetchall()
ix = {c: i for i, c in enumerate(cols)}
g = lambda r, c: r[ix[c]]
def mset(r):
    lp = g(r, 'last_p'); return 100.0 if lp >= 95 else (0.0 if lp <= 5 else lp)
def fresh(r):
    return (g(r,'pre120_c') or 0) >= 1 and 20 <= g(r,'pre120') <= 80 and g(r,'prev_vwap') is not None and 15 <= g(r,'prev_vwap') <= 85
SPORTS = ('football','soccer','baseball','tennis','basketball','hockey','esports','cricket','combat','golf','motorsport','sports')
def sim(L=3, S=100, s=0.10, cd=600, elig=lambda r: True, C=0.0):
    last = {}; f = []
    for r in rows:
        if not elig(r): continue
        tk, t = g(r,'ticker'), g(r,'t')
        for side in ("yes", "no"):
            beyond = g(r, f"ylt{L}" if side == "yes" else f"ngt{L}") or 0.0
            at = g(r, f"yat{L}" if side == "yes" else f"nat{L}") or 0.0
            if beyond + at <= 0: continue
            k = (tk, side)
            if k in last and t - last[k] < cd: continue
            q = min(S, max(0.0, beyond - C) + s * at)   # C = extra competitor size ahead of us at our price or better
            if q <= 1e-9: continue
            last[k] = t
            x = L if side == "yes" else 100 - L; sgn = 1 if side == "yes" else -1
            cat = g(r,'category') or 'unclassified'
            f.append(dict(day=str(g(r,'dday')), hold=sgn*(mset(r)-x)*q/100, q=q, cost=(x if side=="yes" else 100-x)*q/100,
                          cat=cat, sport=any(w in cat for w in SPORTS), ev=tk.split('-')[1] if '-' in tk else tk))
    return f
def summ(f):
    days = collections.defaultdict(float)
    for z in f: days[z['day']] += z['hold']
    dv = [days[str(d)] for d in days_list]; n = len(dv); mu = sum(dv)/n; sd = (sum((v-mu)**2 for v in dv)/(n-1))**.5 if n > 1 else 0
    ev = collections.defaultdict(float)
    for z in f: ev[z['ev']] += z['hold']
    top = sorted(ev.values(), reverse=True); tot = sum(z['hold'] for z in f)
    return dict(fills=len(f), contracts=round(sum(z['q'] for z in f)), hold_total=round(tot), per_day=round(mu), sd_day=round(sd),
                t=round(mu/(sd/n**.5), 2) if sd > 0 else None, days_positive=f"{sum(1 for v in dv if v > 0)}/{n}", worst_day=round(min(dv)),
                top10_events_share=round(sum(top[:10])/tot, 2) if tot > 0 else None)
days_list = days[1:-1]
res = {"label": label, "days": [str(d) for d in days_list], "eligible_rows": len(rows)}
base = sim()
res["base L3 S100 s10%"] = summ(base)
res["through-only s=0"] = summ(sim(s=0.0))
res["fresh-only"] = summ(sim(elig=fresh))
res["non-sports only"] = summ([z for z in base if not z['sport']])
res["sports only"] = summ([z for z in base if z['sport']])
for C in (10, 30, 100):
    res[f"competition C={C}"] = summ(sim(s=0.0, C=C))
cat = collections.defaultdict(float)
for z in base: cat[z['cat']] += z['hold']
res["by_category_hold_per_day"] = {k: round(v/len(days_list)) for k, v in sorted(cat.items(), key=lambda x: -x[1])[:12]}
json.dump(res, open(f"{D}/result.json", "w"), indent=1)
print(json.dumps(res, indent=1), flush=True)
