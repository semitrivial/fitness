from random import random
from fit.classes import Organism, Food, live_organisms

adjacent_deltas = [
  (-1,1), (0,1), (1,1), (-1,0), (1,0), (-1,-1), (0,-1), (1,-1)
]

env_height = 10
env_width = 50

env_map = {}

def init_map():
  for i in range(1000):
    for j in range(1000):
      env_map[i-500,j-500] = None

  for i in range(env_width):
    for j in range(env_height):
      rnd = random()

      if rnd < 1/50:
        env_map[i,j] = Organism(i,j,[])
      elif rnd < 2/50:
        env_map[i,j] = Food(i,j)
      else:
        env_map[i,j] = None

init_map()

original_organisms = live_organisms.copy()

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

def repopulate_food():
  if random() < 1/20:
    for i in range(env_width):
      for j in range(env_height):
        if env_map[i,j] is None:
          if random() < 1/75:
            env_map[i,j] = Food(i,j)