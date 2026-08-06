import math
import random
# from server import get_ball_pos
import pygame as pg


class Ball:
    def __init__(self, size, speed, x, y, d: int = None):
        x = int(x)
        y = int(y)
        self.size = size
        self.speed = speed
        self.x: int = x
        self.y: int = y
        self.direction = random.choice([random.randint(0, 160)] +
                                       [random.randint(200, 360)]) if d is None else d
        self.fx, self.fy = x, y
        self.fs = speed

    def draw(self, screen, /):
        pg.draw.rect(screen, "white", self.get_rect())

    def move(self, dt, /):
        self.x += round(self.speed * dt * math.cos(math.radians(self.direction)))
        self.y += round(self.speed * dt * math.sin(math.radians(self.direction)))

    def touches_line(self, lines, /):
        r = self.get_rect()

        for l in lines:
            if r.clipline(*l()):
                return l

        return None

    def clamp(self, screen, /):
        if self.x < 0:
            self.x = 0

        elif self.x + self.size > screen.get_width():
            self.x = screen.get_width() - self.size

        if self.y < 0:
            self.y = 0

        elif self.y + self.size > screen.get_height():
            self.y = screen.get_height() - self.size

    def get_rect(self, /):
        return pg.Rect(self.x, self.y, self.size, self.size)

    def reset(self, /):
        self.x = self.fx
        self.y = self.fy
        self.speed = self.fs
        self.direction = random.choice([random.randint(0, 160)] + [random.randint(200, 360)])
