from fit.agents.QLearner import QLearner
from fit.map import adjacent_deltas, env_map, display_map, repopulate_food
from fit.map import env_width, env_height, init_map
from fit.obs import gen_obs
from fit.actions import try_to_reproduce, try_to_eat, try_to_move, action_list
from fit.actions import handle_action, modify_ancestor_count
from fit.classes import Organism, Food, live_organisms, all_organisms, reset_organism_ids
from fit.fitness import print_statistics_header, print_statistics, print_run_statistics

from random import random, seed, shuffle
import os
from time import sleep

seed(0)

driver = QLearner(len(action_list))

def age_actor(actor):
  actor.age += 1
  actor.satiety -= 1

  if actor.satiety < 1:
    if random() < 2/3:
      kill_actor(actor)
      return

  if actor.age > 75:
    if random() < .25:
      kill_actor(actor)

def kill_actor(actor):
  env_map[actor.x, actor.y] = None
  live_organisms.remove(actor)

  if len(live_organisms) == 0:
    for organism in all_organisms:
      organism.mark_winner(actor.current_turn)

  modify_ancestor_count(actor, delta=-1, already_checked_set=set())
  actor.isDead = True
  actor.death_turn = actor.current_turn
  if actor.num_live_descendants == 0:
    actor.mark_loser(actor.current_turn)
  if len(live_organisms) == 0:
    actor.mark_winner(actor.current_turn)

def one_turn():
  # Randomly choose order of action, to avoid collisions
  actor_list = sorted(live_organisms, key=lambda actor: (actor.x, actor.y))
  shuffle(actor_list)

  for actor in actor_list:
    actor.current_turn = turns
    age_actor(actor)

    if actor.isDead:
      continue

    prev_obs = gen_obs(actor)
    if actor.isInsane:
      act = driver.insanity_act(prev_obs)
    else:
      act = driver.act(prev_obs)
    actor.prev_act = act
    actor.prev_obs = prev_obs

    reward = handle_action(actor, act)

    actor.prev_reward = reward

  repopulate_food()

  for actor in actor_list:
    if actor.isDead:
      continue
    new_obs = gen_obs(actor)
    driver.train(actor.prev_obs, actor.prev_act, actor.prev_reward, new_obs)

  update_winners_and_losers()

def update_winners_and_losers():
  already_checked_set = set()

  for x in live_organisms:
    update_winners_losers_recurse(x, already_checked_set)

def update_winners_losers_recurse(x, already_checked_set):
  if x in already_checked_set:
    return

  already_checked_set.add(x)

  if x.isWinner:
    return

  if x.num_live_descendants == 0 and not(x in live_organisms):
    x.mark_loser(x.current_turn)

  if x.num_live_descendants == len(live_organisms):
    x.mark_winner(x.current_turn)

  for parent in x.parents:
    # Necessary to call this here because the death of an organism
    # which is not in your descendants can nevertheless trigger
    # your becoming a winner. The code for updating counts only
    # runs on ancestors of the dying organism.
    update_winners_losers_recurse(parent, already_checked_set)

def reset_simulation():
  all_organisms.clear()
  live_organisms.clear()
  reset_organism_ids()
  init_map()

reset_simulation()

turns = 0


# Initial training phase
print("Performing initial training")
while turns < 1000000:
  turns += 1

  if turns % 100 == 0:
    print(f"Finished training step {turns}/10000 (Currently {len(live_organisms)} live organisms)")

  one_turn()
  if len(live_organisms) == 0:
    reset_simulation()

driver.disable_training()

rnd_seed = 1

print_statistics_header()

while True:
  turns = 0

  seed(rnd_seed)

  reset_simulation()

  while turns < 100000:
    turns += 1
    one_turn()

    if len(live_organisms) == 0:
      print(f"Run {rnd_seed} went extinct in {turns} turns")
      break

  went_extinct = len(live_organisms) == 0
  if not went_extinct:
    print(f"Run {rnd_seed} survived {turns} turns")
  print_statistics(run_id=rnd_seed)
  print_run_statistics(
    run_id=rnd_seed,
    random_seed=rnd_seed,
    completed_turns=turns,
    went_extinct=went_extinct,
  )

  rnd_seed += 1

