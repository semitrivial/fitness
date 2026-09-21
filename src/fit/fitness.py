import csv

from fit.classes import all_organisms
from fit.classes import FOOD_NORMAL, STERILE_FUTURE_DESCS, STERILE_ALL_DESCS
from fit.classes import STERILE_FUTURE_DESCS_BONUS, STERILE_ALL_DESCS_BONUS
from fit.classes import APHRODISIAC, INSANITY, SHORTSIGHTED

foodtypes = [FOOD_NORMAL, STERILE_FUTURE_DESCS, STERILE_ALL_DESCS,
  STERILE_FUTURE_DESCS_BONUS, STERILE_ALL_DESCS_BONUS,
  APHRODISIAC, INSANITY, SHORTSIGHTED]

foodtype_names = {
  FOOD_NORMAL: "Normal",
  STERILE_FUTURE_DESCS: "StrlFutDescs",
  STERILE_ALL_DESCS: "StrlAllDescs",
  STERILE_FUTURE_DESCS_BONUS: "StrlFutDescsBonus",
  STERILE_ALL_DESCS_BONUS: "StrlAllDescsBonus",
  APHRODISIAC: "FrtlBonus",
  INSANITY: "Insanity",
  SHORTSIGHTED: "Shortsighted"
}

def print_fitness_scores():
  d = {
    foodtype: {
      'winners_who_ate_it': 0,
      'losers_who_ate_it': 0,
      'score': -1
    } for foodtype in foodtypes
  }

  for x in all_organisms:
    for foodtype in foodtypes:
      if foodtype in x.foods_eaten:
        if x.isWinner:
          d[foodtype]['winners_who_ate_it'] += 1
        if x.isLoser:
          d[foodtype]['losers_who_ate_it'] += 1

  for foodtype in foodtypes:
    total = d[foodtype]['winners_who_ate_it'] + d[foodtype]['losers_who_ate_it']

    if total == 0:
      score = -1
    else:
      score = d[foodtype]['winners_who_ate_it'] / total
    d[foodtype]['score'] = score

    result = f"{foodtype_names[foodtype]}: Score={score}"
    result += f" (Winners: {d[foodtype]['winners_who_ate_it']},"
    result += f" Losers: {d[foodtype]['losers_who_ate_it']})"
    print(result)

def organism_fieldnames():
  fields = [
    "id", "run_id", "organism_id", "parent_ids", "birth_turn", "death_turn",
    "winner_turn", "loser_turn", "isWinner", "isLoser", "isDead",
    "age_at_export", "satiety_at_export", "num_children",
    "sterile_at_export", "future_descendants_sterile_at_export",
    "extra_fertile_at_export", "is_insane_at_export",
    "is_shortsighted_at_export",
  ]
  for foodtype in foodtypes:
    name = foodtype_names[foodtype]
    # The original binary columns remain for compatibility with the existing
    # analysis scripts. The additional columns preserve exposure dose and time.
    fields.extend([
      name, f"{name}_count", f"{name}_first_turn", f"{name}_last_turn",
    ])
  return fields


RUN_FIELDNAMES = [
  "run_id", "random_seed", "completed_turns", "went_extinct",
  "final_population", "organisms_created", "winner_count", "loser_count",
  "both_count", "unresolved_count",
]


def print_statistics_header():
  with open("stats.csv", "w", newline="") as stats_file:
    csv.DictWriter(stats_file, fieldnames=organism_fieldnames()).writeheader()
  with open("runs.csv", "w", newline="") as runs_file:
    csv.DictWriter(runs_file, fieldnames=RUN_FIELDNAMES).writeheader()


def print_statistics(run_id):
  """Append every organism in one run, including unresolved organisms."""
  with open("stats.csv", "a", newline="") as stats_file:
    writer = csv.DictWriter(stats_file, fieldnames=organism_fieldnames())
    for x in sorted(all_organisms, key=lambda organism: organism.organism_id):
      row = {
        # Retain the legacy id column for the existing analysis scripts.
        # run_id makes it unique even though organism_id restarts each run.
        "id": f"{run_id}:{x.organism_id}",
        "run_id": run_id,
        "organism_id": x.organism_id,
        "parent_ids": ";".join(str(parent.organism_id) for parent in x.parents),
        "birth_turn": x.birth_turn,
        "death_turn": x.death_turn,
        "winner_turn": x.winner_turn,
        "loser_turn": x.loser_turn,
        "isWinner": x.isWinner,
        "isLoser": x.isLoser,
        "isDead": x.isDead,
        "age_at_export": x.age,
        "satiety_at_export": x.satiety,
        "num_children": len(x.children),
        "sterile_at_export": x.sterile,
        "future_descendants_sterile_at_export": x.futureDescsSterile,
        "extra_fertile_at_export": x.extraFertile,
        "is_insane_at_export": x.isInsane,
        "is_shortsighted_at_export": x.isShortsighted,
      }
      for foodtype in foodtypes:
        name = foodtype_names[foodtype]
        row[name] = int(foodtype in x.foods_eaten) # Record whether or not the organism ate the food.
        row[f"{name}_count"] = x.food_eaten_counts.get(foodtype, 0)
        row[f"{name}_first_turn"] = x.first_food_eaten_turn.get(foodtype)
        row[f"{name}_last_turn"] = x.last_food_eaten_turn.get(foodtype)
      writer.writerow(row)


def print_run_statistics(run_id, random_seed, completed_turns, went_extinct):
  """Append one manifest row for every run, extinct or surviving."""
  winner_count = sum(x.isWinner and not x.isLoser for x in all_organisms)
  loser_count = sum(x.isLoser and not x.isWinner for x in all_organisms)
  both_count = sum(x.isWinner and x.isLoser for x in all_organisms)
  unresolved_count = sum(not x.isWinner and not x.isLoser for x in all_organisms)
  row = {
    "run_id": run_id,
    "random_seed": random_seed,
    "completed_turns": completed_turns,
    "went_extinct": went_extinct,
    "final_population": sum(not x.isDead for x in all_organisms),
    "organisms_created": len(all_organisms),
    "winner_count": winner_count,
    "loser_count": loser_count,
    "both_count": both_count,
    "unresolved_count": unresolved_count,
  }
  with open("runs.csv", "a", newline="") as runs_file:
    csv.DictWriter(runs_file, fieldnames=RUN_FIELDNAMES).writerow(row)
