# Created by Anthropic Claude Opus 5.5 (via Hermes Agent) for the fit.tex statistical analysis.
# Run from the repository root: .venv/bin/python stats/exploration/fit_bonus.py
# Requires stats/new_results/organisms.parquet.parts (built by stats/analyze_new_export.py).
import duckdb, csv, time
c = duckdb.connect(); c.execute("SET threads TO 8")
P = "read_parquet('stats/new_results/organisms.parquet.parts/*.parquet')"
runs = {int(r["run_id"]): r for r in csv.DictReader(open("runs.csv"))}
surv = sorted(k for k, r in runs.items() if r["went_extinct"] == "False")[::9]  # ~300 runs
S = ",".join(map(str, surv)); t = time.time()
c.execute(f"create table o as select run_id, organism_id, parent_ids, birth_turn, death_turn, isWinner, isLoser, num_children, StrlFutDescs, StrlFutDescs_first_turn a_t, StrlFutDescsBonus, StrlFutDescsBonus_first_turn b_t, FrtlBonus, Normal, Insanity, Shortsighted from {P} where run_id in ({S})")
c.execute("create table e as select run_id, cast(unnest(string_split(parent_ids,';')) as bigint) organism_id, birth_turn cb, isWinner cw from o where parent_ids is not null")
# one row per (eater, food) with fertile kids (born before eating) and sterile kids (after)
c.execute("""create table x as
 select o.run_id, o.organism_id, food, eat, o.isWinner w, o.birth_turn bt, o.death_turn dt, o.num_children k,
   (eat - o.birth_turn) eat_age,
   count(e.cb) filter (where e.cb < eat) fert, count(e.cb) filter (where e.cb >= eat) ster,
   coalesce(max(e.cw::int) filter (where e.cb < eat),0) any_fert_child_winner
 from (select *, 'Plain' food, a_t eat from o where StrlFutDescs>0 and StrlFutDescsBonus=0
       union all select *, 'Bonus', b_t from o where StrlFutDescsBonus>0 and StrlFutDescs=0) o
 left join e using(run_id, organism_id)
 where o.isWinner<>o.isLoser group by all""")
print(f"[built] {time.time()-t:.1f}s; runs={len(surv)}; eaters:", c.execute("select food,count(*) from x group by 1").fetchall())
def show(title, sql):
    print("\n" + title); [print("  ", r) for r in c.execute(sql).fetchall()]
show("food | n | fitness | mean kids | mean fertile | mean sterile | share eaten before 1st child | mean eat age",
     "select food,count(*),round(avg(w::int),4),round(avg(k),3),round(avg(fert),3),round(avg(ster),3),round(avg((fert=0)::int),4),round(avg(eat_age),2) from x group by 1")
show("Fitness by fertile kids (born before eating): fert | Plain n, fit | Bonus n, fit",
     """select least(fert,5) f, count(*) filter(where food='Plain'), round(avg(w::int) filter(where food='Plain'),4),
       count(*) filter(where food='Bonus'), round(avg(w::int) filter(where food='Bonus'),4) from x group by 1 order by 1""")
show("Sterile kids produced after eating, by fertile kids: fert | Plain mean sterile | Bonus mean sterile",
     "select least(fert,5), round(avg(ster) filter(where food='Plain'),3), round(avg(ster) filter(where food='Bonus'),3) from x group by 1 order by 1")
show("CROWDING TEST, fert=1..3: within same fertile count, fitness by sterile kids (Plain+Bonus pooled): fert | ster | n | fit",
     "select fert, least(ster,4), count(*), round(avg(w::int),4) from x where fert between 1 and 3 group by 1,2 order by 1,2")
show("Eat age distribution: age band | Plain share | Bonus share | Plain P(fert=0) | Bonus P(fert=0)",
     """select least(eat_age//10,9)*10 a, round(count(*) filter(where food='Plain')/(select count(*) from x where food='Plain'),4),
      round(count(*) filter(where food='Bonus')/(select count(*) from x where food='Bonus'),4),
      round(avg((fert=0)::int) filter(where food='Plain'),3), round(avg((fert=0)::int) filter(where food='Bonus'),3) from x group by 1 order by 1""")
show("Standardized: Bonus fitness reweighted to Plain's fertile-kid distribution (strata fert 0..5+)",
     """with s as (select least(fert,5) f, avg(w::int) filter(where food='Plain') pp, avg(w::int) filter(where food='Bonus') pb,
       count(*) filter(where food='Plain') np from x group by 1)
       select round(sum(pp*np)/sum(np),5) plain, round(sum(pb*np)/sum(np),5) bonus_std from s""")
show("Among fert>=1 eaters: does a fertile child become the winner? food | P(some pre-eat child is winner) | fitness",
     "select food, round(avg(any_fert_child_winner),4), round(avg(w::int),4) from x where fert>=1 group by 1")
