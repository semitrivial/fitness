from fit.map import adjacent_deltas, env_width, env_height, env_map
from fit.classes import Organism, Food

from random import random

#actions
NORTH = 0
SOUTH = 1
EAST = 2
WEST = 3
EAT = 4
REPRODUCE = 5
action_list = [NORTH, SOUTH, EAST, WEST, EAT, REPRODUCE]


def try_to_reproduce(actor):
  partner = None
  empty = None

  if random()<2/3:
    return 0

  for delta in adjacent_deltas:
    x,y = delta
    x,y = x + actor.x, y + actor.y

    if isinstance(env_map[x,y], Organism):
      if partner is not None:
        return -1
      else:
        partner = env_map[x,y]
    elif env_map[x,y] is None:
      empty = (x,y)

  if (partner is None) or (empty is None):
    return -1

  child = Organism(*empty)
  env_map[empty] = child

  return 10

def try_to_eat(actor):
  for delta in adjacent_deltas:
    x,y = delta
    x += actor.x
    y += actor.y
    if isinstance(env_map[x,y], Food):
      env_map[x,y] = None
      actor.hp = max(10, actor.hp+1)
      actor.satiety = 100
      return 1

  return -1

def try_to_move(actor, act):
  x, y = actor.x, actor.y

  if act == NORTH: y += 1
  if act == SOUTH: y -= 1
  if act == EAST: x += 1
  if act == WEST: x -= 1

  if x >= env_width: x=0
  if x < 0: x=env_width-1
  if y >= env_height: y=0
  if y < 0: y=env_height-1

  if not(env_map[x,y] is None):
    return -1  # Penalize agent and do not allow movement

  env_map[actor.x, actor.y] = None
  env_map[x,y] = actor
  actor.x, actor.y = x,y
  return 0  # Reward 0, successful move

def handle_action(actor, act):
  if act == EAT:
    reward = try_to_eat(actor)
  elif act == REPRODUCE:
    reward = try_to_reproduce(actor)
  else:
    reward = try_to_move(actor, act)

  return reward
