from fit.agents.QLearner import QLearner
from random import random, sample
import os
from time import sleep

env_height = 10
env_width = 50

#actions
NORTH = 0
SOUTH = 1
EAST = 2
WEST = 3
EAT = 4
REPRODUCE = 5
actions = [NORTH, SOUTH, EAST, WEST, EAT, REPRODUCE]

driver = QLearner(len(actions))

class Food:
  def __init__(self, x, y):
    self.x = x
    self.y = y

live_organisms = []

class Organism:
  def __init__(self, x, y):
    self.x = x
    self.y = y
    self.hp = 10
    self.prev_act = None
    self.prev_obs = None
    live_organisms.append(self)

env_map = {}

def init_map():
  for i in range(1000):
    for j in range(1000):
      env_map[i-500,j-500] = None

  for i in range(env_width):
    for j in range(env_height):
      if random() < 1/50:
        env_map[i,j] = Organism(i,j)
      elif random() < 1/50:
        env_map[i,j] = Food(i,j)
      else:
        env_map[i,j] = None

init_map()

def compute_sight(agent, x_delta, y_delta):
  x = agent.x + x_delta
  y = agent.y + y_delta

  if env_map[x,y] == None:
    return " "
  if isinstance(env_map[x,y], Organism):
    return "@"
  # Food
  return "*"

def compute_horizontal_blur(agent, x_delta, y_delta):
  x = agent.x + x_delta
  y = agent.y + y_delta
  i = 0
  while i < 5:
    if isinstance(env_map[x+i,y], Food):
      return "*"
    i += 1

  i = 0
  while i < 5:
    if isinstance(env_map[x+i,y], Organism):
      return "@"
    i += 1

  return " "

def compute_vertical_blur(agent, x_delta, y_delta):
  x = agent.x + x_delta
  y = agent.y + y_delta
  i = 0
  while i < 5:
    if isinstance(env_map[x,y+i], Food):
      return "*"
    i += 1

  i = 0
  while i < 5:
    if isinstance(env_map[x,y+i], QLearner):
      return "@"
    i += 1

  return " "

def gen_obs(agent):
  blurry_north = compute_horizontal_blur(agent, -2, 2)
  blurry_south = compute_horizontal_blur(agent, -2, -2)
  blurry_east = compute_vertical_blur(agent, 2, -2)
  blurry_west = compute_vertical_blur(agent, -2,-2)
  northwest = compute_sight(agent, -1, 1)
  north = compute_sight(agent, 0, 1)
  northeast = compute_sight(agent, 1, 1)
  west = compute_sight(agent, -1, 0)
  east = compute_sight(agent, 1, 0)
  southwest = compute_sight(agent, -1, -1)
  south = compute_sight(agent, 0, -1)
  southeast = compute_sight(agent, 1, -1)

  return (
    blurry_north, blurry_south, blurry_east, blurry_west, northwest, north,
    northeast, west, east, southwest, south, southeast)

def display_map():
  for i in range(env_height):
    txt = ""
    for j in range(env_width):
      if env_map[j,i] == None:
        txt += " "
      elif isinstance(env_map[j,i], Organism):
        txt += "@"
      else:
        txt += "*"
    print(txt)


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
    print("Bad move attempted")
    return -1  # Penalize agent and do not allow movement

  env_map[actor.x, actor.y] = None
  env_map[x,y] = actor
  actor.x, actor.y = x,y
  print("Move succeeded")
  return 0  # Reward 0, successful move

def try_to_eat(actor):
  adjacent_deltas = [
    (-1,1), (0,1), (1,1), (-1,0), (1,0), (-1,-1), (0,-1), (1,-1)
  ]
  for delta in adjacent_deltas:
    x,y = delta
    x += actor.x
    y += actor.y
    if isinstance(env_map[x,y], Food):
      env_map[x,y] = None
      actor.hp = max(10, actor.hp+1)
      return 1

  return -1

def one_turn():
  # Randomly choose order of action, to avoid collisions
  actor_list = sample(live_organisms, len(live_organisms))

  for actor in actor_list:
    prev_obs = gen_obs(actor)
    act = driver.act(prev_obs)
    actor.prev_act = act
    actor.prev_obs = prev_obs

    if act == EAT:
      reward = try_to_eat(actor)
    elif act == REPRODUCE:
      reward = 0
    else:
      reward = try_to_move(actor, act)

    actor.prev_reward = reward

  for actor in actor_list:
    new_obs = gen_obs(actor)
    driver.train(actor.prev_obs, actor.prev_act, actor.prev_reward, new_obs)

for _ in range(1000):
  os.system('clear')
  display_map()
  one_turn()
  sleep(.01)

