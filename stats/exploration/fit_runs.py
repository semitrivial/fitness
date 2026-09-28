# Created by Anthropic Claude Opus 5.5 (via Hermes Agent) for the fit.tex statistical analysis.
# Run from the repository root: .venv/bin/python stats/exploration/fit_runs.py
# Requires stats/new_results/organisms.parquet.parts (built by stats/analyze_new_export.py).
import csv, numpy as np
from collections import defaultdict
runs = {int(r["run_id"]): r for r in csv.DictReader(open("runs.csv"))}
surv = {k for k, r in runs.items() if r["went_extinct"] == "False"}
F = ["Normal","StrlFutDescs","StrlAllDescs","StrlFutDescsBonus","StrlAllDescsBonus","FrtlBonus","Insanity","Shortsighted"]
W = defaultdict(dict); L = defaultdict(dict)
for r in csv.DictReader(open("stats/new_results/food_by_run.csv")):
    k = int(r["run_id"])
    if k in surv: W[r["food"]][k] = int(r["winners"]); L[r["food"]][k] = int(r["losers"])
ids = np.array(sorted(surv)); rng = np.random.default_rng(0); B = 2000
boot = rng.integers(0, len(ids), (B, len(ids)))
M = {f: (np.array([W[f][i] for i in ids]), np.array([L[f][i] for i in ids])) for f in F}
print(f"surviving runs {len(ids)}")
print("food pooled_fit run-cluster-95%CI  mean-of-run-fits  sd-run-fit")
for f in F:
    w, l = M[f]; p = w.sum()/(w+l).sum()
    bs = w[boot].sum(1)/(w+l)[boot].sum(1)
    rf = w[(w+l)>0]/(w+l)[(w+l)>0]
    print(f"{f:18s} {p:.5f} [{np.quantile(bs,.025):.5f},{np.quantile(bs,.975):.5f}] {rf.mean():.5f} {rf.std():.4f}")
def paired(a, b):
    wa, la = M[a]; wb, lb = M[b]; ok = ((wa+la)>0)&((wb+lb)>0)
    d = wa[ok]/(wa+la)[ok] - wb[ok]/(wb+lb)[ok]
    wins = (d > 0).mean()
    bs = [d[rng.integers(0,len(d),len(d))].mean() for _ in range(B)]
    print(f"{a} - {b}: mean run diff {d.mean():+.5f} CI [{np.quantile(bs,.025):+.5f},{np.quantile(bs,.975):+.5f}], a>b in {wins:.1%} of {ok.sum()} runs")
for a, b in [("Normal","Shortsighted"),("StrlFutDescs","StrlFutDescsBonus"),("Normal","Insanity"),("FrtlBonus","Normal")]:
    paired(a, b)
