from fit.classes import Organism, Food
from fit.map import env_map, env_width, env_height


def compute_sight(agent, x_delta, y_delta):
  x = (agent.x + x_delta) % env_width
  y = (agent.y + y_delta) % env_height

  if env_map[x,y] == None:
    return " "
  if isinstance(env_map[x,y], Organism):
    return "@"
  # Food
  return "*"

def compute_horizontal_blur(agent, x_delta, y_delta):
  x = (agent.x + x_delta) % env_width
  y = (agent.y + y_delta) % env_height
  i = 0
  while i < 5:
    if isinstance(env_map[(x+i)%env_width,y], Food):
      return "*"
    i += 1

  i = 0
  while i < 5:
    if isinstance(env_map[(x+i)%env_width,y], Organism):
      return "@"
    i += 1

  return " "

def compute_vertical_blur(agent, x_delta, y_delta):
  x = (agent.x + x_delta) % env_width
  y = (agent.y + y_delta) % env_height
  i = 0
  while i < 5:
    if isinstance(env_map[x,(y+i)%env_height], Food):
      return "*"
    i += 1

  i = 0
  while i < 5:
    if isinstance(env_map[x,(y+i)%env_height], Organism):
      return "@"
    i += 1

  return " "

def gen_obs(agent):
  if agent.isShortsighted:
    blurry_north, blurry_south, blurry_east, blurry_west = " ", " ", " ", " "
  else:
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