# Created by Anthropic Claude Opus 5.5 (via Hermes Agent) for the fit.tex statistical analysis.
# Run from the repository root: .venv/bin/python stats/exploration/fit_cluster.py
# Requires stats/new_results/organisms.parquet.parts (built by stats/analyze_new_export.py).
import duckdb, numpy as np, csv, time
c = duckdb.connect(); c.execute("SET threads TO 8")
P = "read_parquet('stats/new_results/organisms.parquet.parts/*.parquet')"
runs = {int(r["run_id"]): r for r in csv.DictReader(open("runs.csv"))}
surv = sorted(k for k, r in runs.items() if r["went_extinct"] == "False")
S = ",".join(map(str, surv))
F = ["Normal","StrlFutDescs","StrlFutDescsBonus","FrtlBonus","Insanity","Shortsighted"]
t = time.time()
# ---------- 1. Clusters = (run, 5000-turn birth block) ----------
B = 5000
sel = ",".join(f"sum(isWinner::int*({f}>0)::int) w_{f}, sum(({f}>0)::int) n_{f}" for f in F)
rows = c.execute(f"""select run_id, birth_turn//{B} blk, {sel} from {P}
  where isWinner<>isLoser and run_id in ({S}) group by 1,2""").fetchnumpy()
print(f"[clusters] {time.time()-t:.1f}s, {len(rows['run_id'])} run×block clusters", flush=True)
rng = np.random.default_rng(0)
blk = rows["blk"]; nb = int(blk.max()) + 1
print("\nFitness by birth-time block (all surviving runs pooled):")
print("block  " + "  ".join(f"{f[:12]:>12s}" for f in F))
for b in range(nb):
    m = blk == b
    print(f"{b*B:>6d} " + "  ".join(f"{rows['w_'+f][m].sum()/rows['n_'+f][m].sum():12.4f}" for f in F))
print("\nFood | CI: run clusters | CI: run×block clusters | ICC-ish: design effect (block)")
for f in F:
    w, n = rows["w_"+f].astype(float), rows["n_"+f].astype(float)
    p = w.sum()/n.sum()
    idx = rng.integers(0, len(w), (1000, len(w)))
    bb = w[idx].sum(1)/n[idx].sum(1)
    # run-level clusters
    rid = rows["run_id"]; ur, inv = np.unique(rid, return_inverse=True)
    wr, nr = np.bincount(inv, w), np.bincount(inv, n)
    idr = rng.integers(0, len(wr), (1000, len(wr)))
    br = wr[idr].sum(1)/nr[idr].sum(1)
    naive = np.sqrt(p*(1-p)/n.sum())
    print(f"{f:18s} {p:.5f} run±{br.std()*1.96:.5f} block±{bb.std()*1.96:.5f} naive±{naive*1.96:.5f} "
          f"DEFF(run)={(br.std()/naive)**2:.1f} DEFF(block)={(bb.std()/naive)**2:.1f}")
# paired within run×block
m = (rows["n_StrlFutDescs"]>0)&(rows["n_StrlFutDescsBonus"]>0)&(rows["n_Normal"]>0)&(rows["n_Shortsighted"]>0)
for a, b in [("StrlFutDescs","StrlFutDescsBonus"),("Normal","Shortsighted")]:
    d = rows["w_"+a][m]/rows["n_"+a][m] - rows["w_"+b][m]/rows["n_"+b][m]
    bs = [d[rng.integers(0,len(d),len(d))].mean() for _ in range(1000)]
    print(f"paired {a}-{b} within run×block: {d.mean():+.5f} [{np.quantile(bs,.025):+.5f},{np.quantile(bs,.975):+.5f}] n={m.sum()}")
