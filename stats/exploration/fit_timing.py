# Created by Anthropic Claude Opus 5.5 (via Hermes Agent) for the fit.tex statistical analysis.
# Run from the repository root: .venv/bin/python stats/exploration/fit_timing.py
# Requires stats/new_results/organisms.parquet.parts (built by stats/analyze_new_export.py).
import duckdb
c = duckdb.connect()
P = "read_parquet('stats/new_results/organisms.parquet.parts/*.parquet')"
runs = ",".join(str(r) for r in range(1, 3124, 60))  # ~52 runs, spread out
c.execute(f"create table o as select * from {P} where run_id in ({runs})")
c.execute("create table e as select run_id, cast(unnest(string_split(parent_ids,';')) as bigint) pid, birth_turn cb from o where parent_ids is not null")
c.execute("create table fc as select run_id, pid organism_id, min(cb) first_child, count(*) nkids from e group by 1,2")
print("runs sampled:", c.execute("select count(distinct run_id), sum((r.went_extinct)::int) from o join read_csv_auto('runs.csv') r using(run_id)").fetchone())
for f in ["StrlFutDescs", "StrlFutDescsBonus", "Insanity", "FrtlBonus", "Shortsighted"]:
    print(f, c.execute(f"""select case when fc.first_child is null then 'no children'
      when {f}_first_turn < fc.first_child then 'ate before 1st child' else 'ate after 1st child' end t,
      count(*), avg(isWinner::int), avg(num_children) from o left join fc using(run_id, organism_id)
      where {f}>0 and isWinner<>isLoser group by 1 order by 1""").fetchall())
print("children eat check (num_children vs join):", c.execute("select avg((coalesce(nkids,0)=num_children)::int) from o left join fc using(run_id,organism_id)").fetchone())
