# Created by Anthropic Claude Opus 5.5 (via Hermes Agent) for the fit.tex statistical analysis.
# Run from the repository root: .venv/bin/python stats/exploration/fit_explore.py
# Requires stats/new_results/organisms.parquet.parts (built by stats/analyze_new_export.py).
import duckdb, time, json, random
import numpy as np
c = duckdb.connect(); c.execute("SET threads TO 8")
P = "read_parquet('stats/new_results/organisms.parquet.parts/*.parquet')"
FOODS = ["Normal","StrlFutDescs","StrlAllDescs","StrlFutDescsBonus","StrlAllDescsBonus","FrtlBonus","Insanity","Shortsighted"]
R = "(isWinner <> isLoser)"
out = {}
def q(name, sql):
    t = time.time(); r = c.execute(sql).fetchall(); print(f"[{name}] {time.time()-t:.1f}s", flush=True); out[name] = r; return r

# 1. Anomaly: winners among StrlAllDescs eaters -- extinct runs?
q("strlall_winners", f"""select o.run_id, r.went_extinct, count(*) from {P} o join read_csv_auto('runs.csv') r using(run_id)
 where isWinner and (StrlAllDescs>0 or StrlAllDescsBonus>0) group by 1,2 order by 3 desc limit 10""")
q("both_rows", f"select o.run_id, r.went_extinct, count(*) from {P} o join read_csv_auto('runs.csv') r using(run_id) where isWinner and isLoser group by 1,2 order by 3 desc limit 5")
# 2. Food fitness in surviving runs only, and exclusive eaters (ate only that one non-normal food)
nn = FOODS[1:]
excl = " and ".join
sel = ",".join(f"sum(({f}>0)::int*isWinner::int), sum(({f}>0)::int)" for f in FOODS)
only = ",".join(f"sum(({f}>0 and " + " and ".join(f"{g}=0" for g in nn if g!=f) + ")::int*isWinner::int), sum(("+f+">0 and " + " and ".join(f"{g}=0" for g in nn if g!=f) + ")::int)" for f in FOODS)
q("food_exclusive", f"select {only} from {P} where {R}")
q("baseline", f"select sum(isWinner::int), count(*) , sum((num_children>0)::int*isWinner::int), sum((num_children>0)::int) from {P} where {R}")
q("no_food_fitness", f"select sum(isWinner::int), count(*) from {P} where {R} and " + " and ".join(f"{f}=0" for f in FOODS))
# 3. Among parents (>=1 child) food fitness -- removes 'died before eating' confound
q("food_parents", f"select {sel} from {P} where {R} and num_children>0")
# 4. Dose response: count of eats
for f in ["StrlFutDescs","Insanity","Shortsighted","FrtlBonus"]:
    q(f"dose_{f}", f"select least({f}_count,4) k, sum(isWinner::int), count(*) from {P} where {R} group by 1 order by 1")
# 5. Age-matched: fitness by age band for normal vs shortsighted vs insanity
q("age_fit", f"select least(age_at_export/10,10)*10 a, sum(isWinner::int), count(*), sum(isWinner::int*(Shortsighted>0)::int), sum((Shortsighted>0)::int), sum(isWinner::int*(Insanity>0)::int), sum((Insanity>0)::int) from {P} where {R} group by 1 order by 1")
# 6. Time to resolution (winner_turn - birth_turn)
q("resolution", f"select isWinner, quantile_cont(coalesce(winner_turn,loser_turn)-birth_turn,[0.5,0.9,0.99]), max(coalesce(winner_turn,loser_turn)-birth_turn) from {P} where {R} group by 1")
json.dump(out, open("stats/new_results/fit_explore.json","w"), default=str)
