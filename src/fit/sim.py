from fit.agents.QLearner import QLearner
from fit.map import adjacent_deltas, env_map, display_map, repopulate_food
from fit.map import env_width, env_height
from fit.obs import gen_obs
from fit.actions import try_to_reproduce, try_to_eat, try_to_move, action_list
from fit.actions import handle_action
from fit.classes import Organism, Food, live_organisms

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

def one_turn():
  # Randomly choose order of action, to avoid collisions
  actor_list = sample(live_organisms, len(live_organisms))

  for actor in actor_list:
    age_actor(actor)
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

for _ in range(1000):
  os.system('clear')
  display_map()
  one_turn()
  sleep(.01)

