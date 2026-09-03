from random import random

live_organisms = set()

all_organisms = set()

FOOD_NORMAL = 0
STERILE_FUTURE_DESCS = 1
STERILE_ALL_DESCS = 2
STERILE_FUTURE_DESCS_BONUS = 3
STERILE_ALL_DESCS_BONUS = 4
APHRODISIAC = 5
INSANITY = 6
SHORTSIGHTED = 7

class Food:
  def __init__(self, x, y):
    self.x = x
    self.y = y

    rnd = random()
    if rnd < .05:
      foodtype = STERILE_FUTURE_DESCS
    elif rnd < .1:
      foodtype = STERILE_ALL_DESCS
    elif rnd < .15:
      foodtype = STERILE_FUTURE_DESCS_BONUS
    elif rnd < .2:
      foodtype = STERILE_ALL_DESCS_BONUS
    elif rnd < .25:
      foodtype = APHRODISIAC
    elif rnd < .3:
      foodtype = INSANITY
    elif rnd < .35:
      foodtype = SHORTSIGHTED
    else:
      foodtype = FOOD_NORMAL

    self.foodtype = foodtype

class Organism:
  def __init__(self, x, y, parents):
    self.x = x
    self.y = y
    self.parents = parents
    self.children = set()
    self.hp = 10
    self.satiety = 100
    self.prev_act = None
    self.prev_obs = None
    self.age = 0
    self.extraFertile = False
    self.sterile = False
    self.futureDescsSterile = False
    self.isWinner = False
    self.isLoser = False
    self.isDead = False
    self.num_live_descendants = 0
    self.foods_eaten = set()
    self.isShortsighted = False
    self.isInsane = False
    live_organisms.add(self)
    all_organisms.add(self)


