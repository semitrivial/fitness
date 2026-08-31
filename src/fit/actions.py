from fit.map import adjacent_deltas, env_width, env_height, env_map
from fit.classes import Organism, Food, live_organisms
from fit.classes import FOOD_NORMAL, STERILE_FUTURE_DESCS, STERILE_ALL_DESCS
from fit.classes import STERILE_FUTURE_DESCS_BONUS, STERILE_ALL_DESCS_BONUS

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

  if actor.sterile:
    return 0

  if random()<1/3 and not(actor.extraFertile):
    return 0

  for delta in adjacent_deltas:
    x,y = delta
    x,y = (x + actor.x) % env_width, (y + actor.y) % env_height

    if isinstance(env_map[x,y], Organism):
      if partner is not None:
        return -1
      else:
        partner = env_map[x,y]
    elif env_map[x,y] is None:
      empty = (x,y)

  if (partner is None) or (empty is None):
    return -1

  if partner.sterile:
    return 0

  child = Organism(*empty, [actor, partner])
  actor.children.add(child)
  partner.children.add(child)
  env_map[empty] = child

  if actor.futureDescsSterile or partner.futureDescsSterile:
    child.sterile = True

  modify_ancestor_count(child, delta=1, already_checked_set=set())

  return 10

def modify_ancestor_count(x, delta, already_checked_set):
  for parent in x.parents:
    if parent in already_checked_set:
      continue

    already_checked_set.add(parent)

    # if parent.isWinner:
    #   return

    parent.num_live_descendants += delta

    if (parent.num_live_descendants == 0) and parent.isDead:
      parent.isLoser = True
    if parent.num_live_descendants == len(live_organisms):
      parent.isWinner = True

    modify_ancestor_count(parent, delta, already_checked_set)

def try_to_eat(actor):
  for delta in adjacent_deltas:
    x,y = delta
    x += actor.x
    y += actor.y
    if isinstance(env_map[x,y], Food):
      food = env_map[x,y]
      env_map[x,y] = None
      actor.hp = max(10, actor.hp+1)
      actor.satiety = 100

      if food.foodtype != FOOD_NORMAL:
        actor.futureDescsSterile = True
        if food.foodtype in [STERILE_ALL_DESCS, STERILE_ALL_DESCS_BONUS]:
          already_checked_set = set()
          make_all_descs_sterile(actor, already_checked_set)
        if food.foodtype in [STERILE_FUTURE_DESCS_BONUS, STERILE_ALL_DESCS_BONUS]:
          actor.extraFertile = True

      actor.foods_eaten.add(food.foodtype)

      return 1

  return -1

def make_all_descs_sterile(actor, already_checked_set):
  for child in actor.children:
    if child in already_checked_set:
      continue

    already_checked_set.add(child)
    child.sterile = True
    child.futureDescsSterile = True
    make_all_descs_sterile(child, already_checked_set)



def try_to_move(actor, act):
  x, y = actor.x, actor.y

  if act == NORTH: y = (y+1) % env_height
  if act == SOUTH: y = (y-1) % env_height
  if act == EAST: x = (x+1) % env_width
  if act == WEST: x = (x-1) % env_width

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
