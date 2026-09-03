from random import random, randrange

class QLearner:
  """
  Basic Q-learning agent, see https://en.wikipedia.org/wiki/Q-learning.
  """
  def __init__(self, n_actions, epsilon=0.9, learning_rate=0.1, gamma=0.9, **kwags):
    self.n_actions = n_actions
    self.epsilon = epsilon
    self.learning_rate = learning_rate
    self.gamma = gamma
    self.actions = range(self.n_actions)
    self.qtable = {}

  def act(self, obs):
    qtable, epsilon, actions = self.qtable, self.epsilon, self.actions
    maybe_add_obs_to_qtable(qtable, actions, obs)

    if random() > epsilon:
      return randrange(self.n_actions)
    elif all(qtable[obs,a]==0 for a in actions):
      return randrange(self.n_actions)
    else:
      return max(actions, key=lambda a: qtable[obs,a])

  def insanity_act(self, obs):
    qtable, epsilon, actions = self.qtable, self.epsilon, self.actions
    maybe_add_obs_to_qtable(qtable, actions, obs)

    if random() > epsilon:
      return randrange(self.n_actions)
    elif all(qtable[obs,a]==0 for a in actions):
      return randrange(self.n_actions)
    else:
      return min(actions, key=lambda a: qtable[obs,a])

  def train(self, o_prev, a, r, o_next):
    qtable, actions, gamma = self.qtable, self.actions, self.gamma
    maybe_add_obs_to_qtable(qtable, actions, o_prev)
    maybe_add_obs_to_qtable(qtable, actions, o_next)
    qtarget = r + gamma * max([qtable[o_next,actn] for actn in actions])
    qpredict = qtable[o_prev, a]
    qtable[o_prev, a] += self.learning_rate * (qtarget - qpredict)

def maybe_add_obs_to_qtable(qtable, actions, obs):
  if not((obs, 0) in qtable):
    qtable.update({(obs, a): 0 for a in actions})