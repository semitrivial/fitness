# Created by Anthropic Claude Opus 5.5 (via Hermes Agent) for the fit.tex statistical analysis.
# Numbers for the rewritten Section 4 of fit.tex. Run from repo root:
#   .venv/bin/python stats/exploration/fit_section4.py
# Requires stats/new_results/organisms.parquet.parts (built by stats/analyze_new_export.py).
import csv, math, duckdb
c = duckdb.connect(); c.execute("SET threads TO 8")
P = "read_parquet('stats/new_results/organisms.parquet.parts/*.parquet')"
runs = {int(r["run_id"]): r for r in csv.DictReader(open("runs.csv"))}
surv = sorted(k for k, r in runs.items() if r["went_extinct"] == "False")
S = ",".join(map(str, surv))
F = ["Normal","StrlFutDescs","StrlAllDescs","StrlFutDescsBonus","StrlAllDescsBonus","FrtlBonus","Insanity","Shortsighted"]
R = "isWinner <> isLoser"
print("extinct-run audit (both, StrlAll* winners) in surviving runs:",
      c.execute(f"select sum((isWinner and isLoser)::int), sum((isWinner and (StrlAllDescs>0 or StrlAllDescsBonus>0))::int) from {P} where run_id in ({S})").fetchone())
print("surviving runs: resolved, unresolved:", c.execute(f"select sum(({R})::int), sum((not isWinner and not isLoser)::int) from {P} where run_id in ({S})").fetchone())
def wil(w, n, z=1.96):
    p = w/n; d = 1+z*z/n; m = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d; ctr = (p+z*z/(2*n))/d
    return ctr-m, ctr+m
print("\nchildren (surviving runs): k, winners, losers, fit, wilson")
for k, w, n in c.execute(f"select least(num_children,14), sum(isWinner::int), count(*) from {P} where {R} and run_id in ({S}) group by 1 order by 1").fetchall():
    lo, hi = wil(w, n); print(k, w, n-w, f"{w/n:.4f}", f"[{lo:.4f},{hi:.4f}]")
sel = ",".join(f"sum(isWinner::int*({f}>0)::int), sum(({f}>0)::int)" for f in F)
r = c.execute(f"select {sel} from {P} where {R} and run_id in ({S}) and birth_turn >= 5000 and birth_turn < 95000").fetchone()
print("\ntrimmed (birth 5k-95k) food fitness:")
for i, f in enumerate(F): print(f, r[2*i], r[2*i+1], f"{r[2*i]/r[2*i+1]:.5f}")
# Timing: 304-run sample (every 9th surviving run), before vs after first child
T = ",".join(map(str, surv[::9]))
c.execute(f"create table o as select * from {P} where run_id in ({T})")
c.execute("create table fc as select run_id, cast(unnest(string_split(parent_ids,';')) as bigint) organism_id, birth_turn cb from o where parent_ids is not null")
c.execute("create table f1 as select run_id, organism_id, min(cb) first_child from fc group by 1,2")
print("\ntiming (304 runs): food, group, n, fitness")
for f in F:
    for row in c.execute(f"""select case when first_child is null then 'none' when {f}_first_turn < first_child then 'before' else 'after' end g,
        count(*), avg(isWinner::int) from o left join f1 using(run_id, organism_id) where {f}>0 and {R} group by 1 order by 1""").fetchall():
        print(f, row[0], row[1], f"{row[2]:.4f}")
print("\nno food / any food (surviving):", c.execute(f"select sum(isWinner::int), count(*) from {P} where {R} and run_id in ({S}) and " + " and ".join(f"{f}=0" for f in F)).fetchone())
