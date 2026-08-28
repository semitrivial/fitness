live_organisms = set()

# Players are organisms which are not yet winners or losers
players = set()

class Food:
  def __init__(self, x, y):
    self.x = x
    self.y = y

class Organism:
  def __init__(self, x, y, parents):
    self.x = x
    self.y = y
    self.parents = parents
    self.hp = 10
    self.satiety = 100
    self.prev_act = None
    self.prev_obs = None
    self.age = 0
    self.isWinner = False
    self.isLoser = False
    self.num_live_descendants = 0
    live_organisms.add(self)
    players.add(self)


