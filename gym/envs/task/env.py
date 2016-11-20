import time
import numpy as np

import gym
from gym import spaces
from gym.utils import seeding

from .game import Game, State, TaskType, action_types

class EasyEnv(gym.Env):
    def __init__(self, task_type=TaskType.pick):
        self.game = Game(10, 10, 6, 6, task_type=task_type)
        self.step_cnt = 0
        self.max_step = 500
        self.spf = 0.01
        self.show_gui = False

        self._seed()

        self.action_space = spaces.Discrete(len(action_types))
        self.observation_space = spaces.Box(0., 1., self.game.image_shape)
        self.reward_range = (-1., 6.)

    def _seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        self.game._seed(self.np_random)
        return [seed]

    def _reset(self):
        self.step_cnt = 0
        self.game.init(self.show_gui)
        self.game.render()
        return self.game.get_bitmap()

    def _step(self, action):
        action = int(action)
        assert 0 <= action < self.action_space.n
        
        rew = self.game.step(action)
        self.game.render()
        obs = self.game.get_bitmap()
        self.step_cnt += 1
        done = self.step_cnt >= self.max_step or self.game.state == State.end
        info = None

        if self.show_gui:
            time.sleep(self.spf)
        # if rew != 0:
            # print(rew)
        return obs, rew, done, info

    def _configure(self, show_gui=False, spf=None):
        self.show_gui = show_gui
        if spf is not None:
            self.spf = spf

if __name__ == '__main__':
    env = EasyEnv()
    env.configure(show_gui=True)
    env.reset()

    while True:
        a = np.random.randint(len(action_types))
        obs, rew, done, info = env.step(a)
        print(rew, done)
        if done:
            break



    
