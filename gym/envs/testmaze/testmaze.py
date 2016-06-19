"""
Classic cart-pole system implemented by Rich Sutton et al.
Copied from https://webdocs.cs.ualberta.ca/~sutton/book/code/pole.c
"""

import logging
import math
import gym
from gym import spaces
from gym.utils import seeding
import numpy as np

logger = logging.getLogger(__name__)

UP = 0
DOWN = 1
RIGHT = 2
LEFT = 3

class TestMaze(gym.Env):
    metadata = {
        'render.modes': ['human', 'rgb_array'],
        'video.frames_per_second' : 50
    }

    def __init__(self):
        self.action_space = spaces.Discrete(6)
        self.width = 10
        self.height = 10
        self.observation_space = spaces.Box(low=0, high=1, shape=(self.height * 2 - 1, self.width * 2 - 1, 3))

        self._seed()
        self.reset()
        self.viewer = None

        self.steps_beyond_done = None

    def _seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def _step(self, action):
        action = action
        assert type(action) == int and action >= 0 and action < self.action_space.n, "%r (%s) invalid"%(action, type(action))

        if action == UP:
            self.y -= 1
        elif action == DOWN:
            self.y += 1
        elif action == LEFT:
            self.x -= 1
        elif action == RIGHT:
            self.x += 1


        reward = 0.0
        done = False
        if self.nstep >= 40:
            done = True

        if self.x < 0 or self.x >= self.width or self.y < 0 or self.y >= self.height:
            reward = -1
            self.x = min(max(self.x, 0), self.width-1)
            self.y = min(max(self.y, 0), self.height-1)
        elif self.state[self.y, self.x] > 0.5:
            done = True
            reward = 1.0

        self.nstep += 1

        return self._gen_observation(), reward, done, {}

    def _reset(self):
        self.nstep = 0
        self.state = np.zeros((self.height, self.width))
        self.y = self.np_random.randint(0, self.height)
        self.x = self.np_random.randint(0, self.width)

        gy = self.np_random.randint(0, self.height)
        gx = self.np_random.randint(0, self.width)
        self.state[gy, gx] = 1

        return self._gen_observation()

    def _gen_observation(self):
        ret = np.zeros(self.observation_space.shape)

        for i in range(self.height):
            for j in range(self.width):
                ni = i - self.y + self.height - 1
                nj = j - self.x + self.width - 1
                if ni >= 0 and ni < ret.shape[0] and nj >= 0 and nj < ret.shape[1]:
                    ret[ni, nj, 0] = 1
                    ret[ni, nj, 1] = (1 if i == self.y and j == self.x else 0)
                    ret[ni, nj, 2] = self.state[i, j]

        return ret

    def _render(self, mode='human', close=False):
        obs = self._gen_observation()
        for i in range(obs.shape[0]):
            s = ''
            for j in range(obs.shape[1]):
                z = int(obs[i, j, 0] + 2 * obs[i, j, 1] + 4 * obs[i, j, 2])
                s += str(z)
            print(s)
        print('========')

        # print(self.state, (self.x, self.y))
        return 'CONCON'
        if close:
            if self.viewer is not None:
                self.viewer.close()
                self.viewer = None
            return

        screen_width = 600
        screen_height = 400

        world_width = self.x_threshold*2
        scale = screen_width/world_width
        carty = 100 # TOP OF CART
        polewidth = 10.0
        polelen = scale * 1.0
        cartwidth = 50.0
        cartheight = 30.0

        if self.viewer is None:
            from gym.envs.classic_control import rendering
            self.viewer = rendering.Viewer(screen_width, screen_height)
            l,r,t,b = -cartwidth/2, cartwidth/2, cartheight/2, -cartheight/2
            axleoffset =cartheight/4.0
            cart = rendering.FilledPolygon([(l,b), (l,t), (r,t), (r,b)])
            self.carttrans = rendering.Transform()
            cart.add_attr(self.carttrans)
            self.viewer.add_geom(cart)
            l,r,t,b = -polewidth/2,polewidth/2,polelen-polewidth/2,-polewidth/2
            pole = rendering.FilledPolygon([(l,b), (l,t), (r,t), (r,b)])
            pole.set_color(.8,.6,.4)
            self.poletrans = rendering.Transform(translation=(0, axleoffset))
            pole.add_attr(self.poletrans)
            pole.add_attr(self.carttrans)
            self.viewer.add_geom(pole)
            self.axle = rendering.make_circle(polewidth/2)
            self.axle.add_attr(self.poletrans)
            self.axle.add_attr(self.carttrans)
            self.axle.set_color(.5,.5,.8)
            self.viewer.add_geom(self.axle)
            self.track = rendering.Line((0,carty), (screen_width,carty))
            self.track.set_color(0,0,0)
            self.viewer.add_geom(self.track)

        x = self.state
        cartx = x[0]*scale+screen_width/2.0 # MIDDLE OF CART
        self.carttrans.set_translation(cartx, carty)
        self.poletrans.set_rotation(-x[2])

        return self.viewer.render(return_rgb_array = mode=='rgb_array')
