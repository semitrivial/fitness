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

def print_statistics_header():
  stats_file = open("stats.csv", "w")

  foods_eaten_str = ""
  for foodtype in foodtypes:
    foods_eaten_str += foodtype_names[foodtype] + ","

  stats_file.write(f"id,isWinner,isLoser,{foods_eaten_str}num_children\n")
  stats_file.flush()
  stats_file.close()

def print_statistics():
  stats_file = open("stats.csv", "a")

  for x in all_organisms:
    if (x.isWinner) or (x.isLoser):
      foods_eaten_str = ""
      for foodtype in foodtypes:
        if foodtype in x.foods_eaten:
          foods_eaten_str += "1"
        else:
          foods_eaten_str += "0"
        foods_eaten_str += ","

      stats_file.write(f"{id(x)},{x.isWinner},{x.isLoser},{foods_eaten_str}{len(x.children)}\n")

  stats_file.flush()
  stats_file.close()
