from fit.agents.QLearner import QLearner
from fit.map import adjacent_deltas, env_map, display_map, repopulate_food
from fit.map import env_width, env_height, original_organisms
from fit.obs import gen_obs
from fit.actions import try_to_reproduce, try_to_eat, try_to_move, action_list
from fit.actions import handle_action, modify_ancestor_count
from fit.classes import Organism, Food, live_organisms, all_organisms
from fit.fitness import print_fitness_scores

from random import random, sample
import os
from time import sleep

driver = QLearner(len(action_list))

def age_actor(actor):
  actor.age += 1
  actor.satiety -= 1

  if actor.satiety < 1:
    if random() < 1/3:
      kill_actor(actor)
      return

  if actor.age > 100:
    if random() < .25:
      kill_actor(actor)

def kill_actor(actor):
  env_map[actor.x, actor.y] = None
  live_organisms.remove(actor)

  if len(live_organisms) == 0:
    for organism in all_organisms:
      organism.isWinner = True

  modify_ancestor_count(actor, delta=-1, already_checked_set=set())
  actor.isDead = True
  if actor.num_live_descendants == 0:
    actor.isLoser = True
  if len(live_organisms) == 0:
    actor.isWinner = True

def one_turn():
  # Randomly choose order of action, to avoid collisions
  actor_list = sample(list(live_organisms), len(live_organisms))

  for actor in actor_list:
    age_actor(actor)

    if actor.isDead:
      continue

    prev_obs = gen_obs(actor)
    act = driver.act(prev_obs)
    actor.prev_act = act
    actor.prev_obs = prev_obs

    reward = handle_action(actor, act)

    actor.prev_reward = reward

  repopulate_food()

  for actor in actor_list:
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
    x.isLoser = True

  if x.num_live_descendants == len(live_organisms):
    x.isWinner = True

  for parent in x.parents:
    update_winners_losers_recurse(parent, already_checked_set)

while True:
  os.system('clear')
  display_map()
  one_turn()
  print(len(live_organisms))

  for x in original_organisms:
    print(f"{id(x)} has {x.num_live_descendants} descs; Winner: {x.isWinner}, Loser: {x.isLoser}")

  print_fitness_scores()

  sleep(.01)

