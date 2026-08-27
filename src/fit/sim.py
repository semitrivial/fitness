from fit.agents.QLearner import QLearner
from random import random

env_height = 50
env_width = 50

class Food:
  pass

class Organism:
  def __init__(self, x, y):
    self.x = x
    self.y = y

env_map = {}

def init_map():
  for i in range(env_width):
    for j in range(env_height):
      if random() < 1/3:
        env_map[i,j] = Organism(i,j)
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
    if isinstance(env_map[x][y+i], Food):
      return "*"
    i += 1

  i = 0
  while i < 5:
    if isinstance(env_map[x][y+i], QLearner):
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