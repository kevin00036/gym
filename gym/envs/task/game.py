import numpy as np
from enum import IntEnum

from PIL import Image, ImageDraw, ImageTk
from tkinter import Tk, Toplevel, Canvas, Frame, NW, NE

class TaskType(IntEnum):
    pick = 0b1
    put = 0b10
    both = 0b11

State = IntEnum('State', ['picked', 'start', 'end'])

action_types = [ 'up', 'down', 'left', 'right', 'pick', 'put', ]
Action = IntEnum('State', action_types)

Movesets = [Action.up, Action.down, Action.left, Action.right]

class Game:

    gui_amp = 4
    FPS = 20

    def __init__(self, width, height, block_width, block_height,
                 *, task_type=TaskType.pick, human_play=False,
                 np_random=None):
        self.width = width
        self.height = height
        self.block_width = block_width
        self.block_height = block_height
        self.frame_width = width * block_width
        self.frame_height = height * block_height
        self.image = Image.new('RGB', (self.frame_width, self.frame_height),
                               'black')
        self.image_shape = (self.frame_height, self.frame_width, 3)
        self.draw = ImageDraw.Draw(self.image)

        self.state =None
        self.first_pick = True
        self.task_type = task_type

        self.player_pos = None
        self.obj_pos = None
        self.mark_pos = None

        if np_random is None:
            np_random = np.random.RandomState()
        self.randint = np_random.randint

        self.human_play = human_play
        if human_play:
            self.last_act = None

        self.tk = None

    def _seed(self, np_random):
        self.randint = np_random.randint
    
    def _randpos(self, disables=[]):
        pos = (self.randint(self.width), self.randint(self.height))
        while pos in disables:
            pos = (self.randint(self.width), self.randint(self.height))
        return pos

    def init(self, show_gui=False):
        self.show_gui = show_gui
        if show_gui:
            if self.tk is not None:
                self.tk.destroy()
            self.tk = Tk()
            self.canvas = Canvas(self.tk, 
                                 width=self.frame_width * self.gui_amp, 
                                 height=self.frame_height * self.gui_amp)
            self.canvas.pack()

        self.player_pos = self._randpos()

        self.first_pick = True
        self.state = State.start
        if self.task_type & TaskType.pick:
            self.obj_pos = self._randpos()
        else:
            self.state = State.picked
        if self.task_type & TaskType.put:
            self.mark_pos = self._randpos([self.obj_pos])

    def _get_frame_pos(self, pos):
        px = pos[0] * self.block_width + self.block_width // 2
        py = pos[1] * self.block_height + self.block_height // 2
        return px, py

    def step(self, act):
        if act is None:
            return 0
        rew = 0
        if act in Movesets:
            x, y = self.player_pos
            nx, ny = self.player_pos
            if act == Action.up:
                (nx, ny) = (x, y-1)
            elif act == Action.down:
                (nx, ny) = (x, y+1)
            elif act == Action.left:
                (nx, ny) = (x-1, y)
            elif act == Action.right:
                (nx, ny) = (x+1, y)
            real_pos = (
                max(0, min(self.width-1, nx)),
                max(0, min(self.height-1, ny)),
            )
            
            self.player_pos = real_pos
            pen = 0 if real_pos == (nx, ny) else -1
            rew += pen
        elif act == Action.pick and self.state == State.start:
            if self.obj_pos == self.player_pos:
                self.state = State.picked
                if self.first_pick:
                    self.first_pick = False
                    rew += 1
                if (not self.task_type & TaskType.put):
                    self.state = State.end
        elif act == Action.put and self.state == State.picked:
            if self.mark_pos == self.player_pos:
                self.state = State.end
                rew += 1
            else:
                self.state = State.start
                self.obj_pos = self.player_pos

        if self.state == State.end:
            rew += 5
        return rew

    def render(self):
        # clear canvas
        self.draw.rectangle((0, 0, self.frame_width, self.frame_height),
                            fill='black')

        # draw obj
        if self.obj_pos and self.state == State.start:
            px, py = self._get_frame_pos(self.obj_pos)
            self.draw.rectangle((px - 2, py - 2, px + 2, py + 2), fill='green')
            
        # draw mark
        if self.mark_pos:
            px, py = self._get_frame_pos(self.mark_pos)
            self.draw.rectangle((px - 2, py - 2, px + 2, py + 2), outline='white')

        # draw player
        px, py = self._get_frame_pos(self.player_pos)
        loc = (px - 2, py - 2, px + 2, py + 2)
        if self.state == State.picked:
            self.draw.ellipse(loc, fill=(0, 255, 255, 0))
        else:
            self.draw.ellipse(loc, fill='blue')

        if self.show_gui:
            gui_img = self.image.resize((self.frame_width * self.gui_amp,
                                         self.frame_height * self.gui_amp))
            self.pi = ImageTk.PhotoImage(gui_img)
            canvas_img = self.canvas.create_image(0, 0, anchor=NW,
                                                  image=self.pi)
            # self.canvas.create_text((self.width*self.gui_amp-20, 5), 
                                    # fill='white', text=str(self.))

            if not self.human_play:
                self.tk.update()

    def get_bitmap(self):
        arr = np.array(self.image.getdata()).reshape(self.image_shape)
        return arr.astype('float32') / 256.0

    def gui_step(self):
        if self.last_act is not None:
            rew = self.step(self.last_act)
            self.last_act = None
        else:
            rew = self.step(None)
        if abs(rew) > 1e-9:
            print('Get reward = %.2f' % rew)
        self.render()
        self.tk.after(1000//self.FPS, self.gui_step)

    def gui_start(self):
        self.canvas.bind("<Key>", self.gui_onkey)
        self.canvas.focus_set()
        self.tk.after(1000//self.FPS, self.gui_step)
        self.tk.mainloop()

    def gui_onkey(self, event):
        if event.keycode == 111 or event.keycode == 8320768:
            self.last_act = Action.up
        elif event.keycode == 116 or event.keycode == 8255233:
            self.last_act = Action.down
        elif event.keycode == 113 or event.keycode == 8124162:
            self.last_act = Action.left
        elif event.keycode == 114 or event.keycode == 8189699:
            self.last_act = Action.right
        elif event.keycode == 53 or event.keycode == 458872:
            self.last_act = Action.pick
        elif event.keycode == 52 or event.keycode == 393338:
            self.last_act = Action.put

if __name__ == '__main__':
    game = Game(10, 10, 6, 6, task_type=TaskType.both, human_play=True)
    game.init(True)
    game.gui_start()
