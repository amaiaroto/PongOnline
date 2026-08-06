import pygame as pg


class Paddle:
    def __init__(self, x, y, w, h, s, /, c="white", side=None):
        self.x = int(x)
        self.y = int(y)
        self.width = w
        self.height = h
        self.color = c
        self.speed = s
        self.side = side

    def draw(self, screen, /):
        pg.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))

    def move(self, delta_x, delta_y, /):
        """
        Moves the paddle
        :param delta_x: never used (if it were to be used it would be positive)
        :param delta_y: negative
        """

        self.x += int(delta_x)
        self.y += int(delta_y)
