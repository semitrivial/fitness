# Created by Anthropic Claude Opus 5.5 (via Hermes Agent) for the fit.tex statistical analysis.
# Figure for Section 4 of fit.tex: fitness vs. number of children, surviving runs only,
# 95% Wilson intervals, 14+ children pooled. Run from repo root:
#   .venv/bin/python stats/exploration/fit_fig_children.py
import csv, math
import duckdb, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
P = "read_parquet('stats/new_results/organisms.parquet.parts/*.parquet')"
surv = [r["run_id"] for r in csv.DictReader(open("runs.csv")) if r["went_extinct"] == "False"]
rows = duckdb.connect().execute(f"""select least(num_children,14), sum(isWinner::int), count(*) from {P}
  where isWinner<>isLoser and run_id in ({','.join(surv)}) group by 1 order by 1""").fetchall()
k, p, lo, hi, n = [], [], [], [], []
for c, w, t in rows:
    z = 1.96; q = w/t; d = 1+z*z/t; ctr = (q+z*z/(2*t))/d; m = z*math.sqrt(q*(1-q)/t+z*z/(4*t*t))/d
    k.append(c); p.append(q); lo.append(q-(ctr-m)); hi.append(ctr+m-q); n.append(t)
plt.rcParams.update({"font.family": "serif", "font.size": 10, "pdf.fonttype": 42})
fig, (a, b) = plt.subplots(1, 2, figsize=(8.4, 3.6), constrained_layout=True)
for ax in (a, b):
    ax.errorbar(k, p, yerr=[lo, hi], fmt="o-", color="#245a75", ms=4.5, mfc="white", capsize=3, lw=1.5)
    ax.set_xlabel("Number of children"); ax.grid(axis="y", color="#d9dee2", lw=.7)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_xticks(k, [str(x) for x in k[:-1]] + ["14+"], fontsize=8)
a.set_ylabel("Fitness (winner proportion)"); a.set_ylim(-.02, 1.02); a.set_title("Full range")
b.set_ylim(.955, 1.0); b.set_xlim(2.5, 14.5); b.set_title("Detail, 3+ children")
fig.savefig("stats/fitness_by_children.pdf")
print("wrote stats/fitness_by_children.pdf", list(zip(k, n)))
