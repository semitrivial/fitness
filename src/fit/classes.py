from random import random

live_organisms = set()

all_organisms = set()

# IDs are reset for every measurement run so ``organism_id`` is meaningful
# only together with the exported ``run_id``.
next_organism_id = 1

def reset_organism_ids():
  global next_organism_id
  next_organism_id = 1

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
  def __init__(self, x, y, parents, birth_turn=0):
    global next_organism_id

    self.organism_id = next_organism_id
    next_organism_id += 1
    self.x = x
    self.y = y
    self.parents = parents
    self.children = set()
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
    self.food_eaten_counts = {}
    self.first_food_eaten_turn = {}
    self.last_food_eaten_turn = {}
    self.isShortsighted = False
    self.isInsane = False
    self.birth_turn = birth_turn
    self.death_turn = None
    self.winner_turn = None
    self.loser_turn = None
    self.current_turn = birth_turn
    live_organisms.add(self)
    all_organisms.add(self)

  def mark_winner(self, turn):
    self.isWinner = True
    if self.winner_turn is None:
      self.winner_turn = turn

  def mark_loser(self, turn):
    self.isLoser = True
    if self.loser_turn is None:
      self.loser_turn = turn


