import random
import socket
import threading
from typing import Any
import sys

import pygame as pg

import ball
import paddle

pg.init()
running = True
# VARIABLE*: TYPE** = VALUE
# *screaming snake case
# **usually int

# PLAYER SETTINGS
MAX_PLAYERS: int = 2
CURRENT_PLAYERS: int = 0

# SCREEN SETTINGS
SCREEN_WIDTH: int = 800
SCREEN_HEIGHT: int = 600
SCREEN_OPTIONS: list[int] = []

# PADDLE SETTINGS
PADDLE_SPEED: int = 5
PADDLE_WIDTH: int = 20
PADDLE_HEIGHT: int = 200
CLOCK: pg.time.Clock = pg.time.Clock()
# BALL SETTINGS
BALL_SIZE: int = 10
BALL_SPEED = 0.25
BG_COLOR: tuple[int, int, int] = (0, 0, 0)
BALL: ball.Ball = ball.Ball(BALL_SIZE, BALL_SPEED, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
PADDLE_LEFT: paddle.Paddle = paddle.Paddle(50, (SCREEN_HEIGHT / 2) - (PADDLE_HEIGHT / 2), PADDLE_WIDTH,
                                           PADDLE_HEIGHT, PADDLE_SPEED, side='L')
PADDLE_RIGHT: paddle.Paddle = paddle.Paddle(SCREEN_WIDTH - (50 + PADDLE_WIDTH),
                                            (SCREEN_HEIGHT / 2) - (PADDLE_HEIGHT / 2),
                                            PADDLE_WIDTH, PADDLE_HEIGHT,
                                            PADDLE_SPEED, side='R')

s_text: pg.font.Font = pg.font.Font(None, 52)
SCORE: list[int] = [0, 0]
CLIENTS: dict[str | None, int | None] = {}

# SERVER_SOCKET: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# SERVER_SOCKET.bind((socket.gethostname(), 8080))
# SERVER_SOCKET.listen(MAX_PLAYERS)

screen: pg.Surface = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
top = lambda: (0, 0, SCREEN_WIDTH, 0)
bottom = lambda: (0, SCREEN_HEIGHT - 1, SCREEN_WIDTH, SCREEN_HEIGHT - 1)
left = lambda: (0, 0, 0, SCREEN_HEIGHT)
right = lambda: (SCREEN_WIDTH - 1, 0, SCREEN_WIDTH - 1, SCREEN_HEIGHT)

sides = [top, bottom, left, right]

# PaddleL borders
paddleL_top = lambda: (PADDLE_LEFT.x, PADDLE_LEFT.y, PADDLE_LEFT.x + PADDLE_LEFT.width, PADDLE_LEFT.y)
paddleL_bottom = lambda: (PADDLE_LEFT.x, PADDLE_LEFT.y + PADDLE_LEFT.height - 1, PADDLE_LEFT.x + PADDLE_LEFT.width - 1,
                          PADDLE_LEFT.y + PADDLE_LEFT.height - 1)
paddleL_right = lambda: (PADDLE_LEFT.x + PADDLE_LEFT.width, PADDLE_LEFT.y, PADDLE_LEFT.x + PADDLE_LEFT.width,
                         PADDLE_LEFT.y + PADDLE_LEFT.height)

paddleL_sides = [paddleL_top, paddleL_bottom, paddleL_right]

# PaddleR Borders
paddleR_top = lambda: (PADDLE_RIGHT.x, PADDLE_RIGHT.y, PADDLE_RIGHT.x + PADDLE_RIGHT.width, PADDLE_RIGHT.y)
paddleR_bottom = lambda: (PADDLE_RIGHT.x, PADDLE_RIGHT.y + PADDLE_RIGHT.height - 1,
                          PADDLE_RIGHT.x + PADDLE_RIGHT.width - 1,
                          PADDLE_RIGHT.y + PADDLE_RIGHT.height - 1)
paddleR_left = lambda: (PADDLE_RIGHT.x, PADDLE_RIGHT.y, PADDLE_RIGHT.x,
                        PADDLE_RIGHT.y + PADDLE_RIGHT.height)

paddleR_sides = [paddleR_top, paddleR_bottom, paddleR_left]

all_paddle_sides = paddleL_sides + paddleR_sides


def get_ball_pos() -> tuple[float, float]:
    """
    Gets the ball's position and returns the result.
    :return: the current position of the ball
    """

    global BALL

    return BALL.x, BALL.y


def pygame_run_function():
    """
    The main thread running pygame. Also makes some communications.
    Not in a separate thread because pygame only works on the main thread.
    """

    global SCORE, running

    previous_touch = None
    while running:
        pg.event.get()

        screen.fill(BG_COLOR)

        PADDLE_LEFT.draw(screen)
        BALL.draw(screen)
        PADDLE_RIGHT.draw(screen)

        BALL.move(CLOCK.get_time())
        BALL.clamp(screen)

        touched_side = BALL.touches_line(sides)

        if touched_side:
            if previous_touch != touched_side:
                previous_touch = touched_side

                if touched_side in {top, bottom}:
                    BALL.direction = -BALL.direction

                if touched_side == right:
                    SCORE[0] += 1
                    BALL.reset()

                if touched_side == left:
                    SCORE[1] += 1
                    BALL.reset()

        touched_side_paddle = BALL.touches_line(all_paddle_sides)

        if touched_side_paddle:
            if previous_touch != touched_side_paddle:
                previous_touch = touched_side_paddle

                if touched_side_paddle in {paddleL_top, paddleL_bottom}:
                    BALL.direction = -BALL.direction + random.randint(-10, 10)

                if touched_side_paddle == paddleL_right:
                    BALL.direction = 180 - BALL.direction + random.randint(-10, 10)

                if touched_side_paddle in {paddleR_top, paddleR_bottom}:
                    BALL.direction = -BALL.direction + random.randint(-10, 10)

                if touched_side_paddle == paddleR_left:
                    BALL.direction = 180 - BALL.direction + random.randint(-10, 10)

                BALL.speed += 0.001

        score_text = s_text.render(f'{SCORE[0]} | {SCORE[1]}', True, "blue")
        screen.blit(score_text, ((screen.get_width() / 2) - (score_text.get_width() / 2), 25))

        CLOCK.tick(60)
        pg.display.flip()
        # socket_things()

def client_processor(conn,addr):
    global running
    print("connection from",addr)
    with conn:
        conn.settimeout(0)
        while running:
            try:
                data = conn.recv(2)

                if not data:
                    continue

                if data[0] == ord('L') or data[0] == ord('R'):
                    paddle = PADDLE_LEFT
                    if data[0] == ord('R'):
                        paddle = PADDLE_RIGHT
                    amount = int.from_bytes(data[1:2], signed=True)

                    if paddle.y > 0 > amount:
                        # move down
                        paddle.move(0, amount)

                    if paddle.y + paddle.height < screen.get_height() and amount > 0:
                        # move up
                        paddle.move(0, amount)

                elif data[0] == ord('G'):
                    conn.send(get_game_state_bytes())
            except BaseException as e:
                pass
                #print("Error", e)

def socket_things():
    global running
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("0.0.0.0", int(sys.argv[1])))
        s.listen(5)
        while running:
            print("listening")
            conn, addr = s.accept()
            socket_thread = threading.Thread(target=client_processor,args=(conn,addr))
            socket_thread.start()


def get_game_state() -> dict[str, Any]:
    """
    Fetches the statuses of things and puts in a dictionary with keys corresponding to the value name, then returns it.
    :return: the resulting dictionary in which the game state is stored.
    """

    return {
        'BX': BALL.x, 'BY': BALL.y, "BSZ": BALL.size, 'BD': BALL.direction, 'SCR': SCORE,
        "LPX": PADDLE_LEFT.x, 'LPY': PADDLE_LEFT.y, 'LPW': PADDLE_LEFT.width, 'LPH': PADDLE_LEFT.height,
        'RPX': PADDLE_RIGHT.x, "RPY": PADDLE_RIGHT.y, 'RPW': PADDLE_RIGHT.width, "RPH": PADDLE_RIGHT.height}


def decode_game_state(b: bytearray):
    p = 0

    def convert():
        nonlocal p
        p += 2
        return int.from_bytes(b[p - 2:p], signed=True)

    return \
        {
            'BX': convert(),
            'BY': convert(),
            'BSZ': convert(),
            'BD': convert(),
            'SCR0': convert(),
            'SCR1': convert(),
            'LPX': convert(),
            'LPY': convert(),
            'LPW': convert(),
            'LPH': convert(),
            'RPX': convert(),
            'RPY': convert(),
            'RPW': convert(),
            'RPH': convert()
        }


def get_game_state_bytes() -> bytearray:
    """
    Gets all the values and puts them in a bytearray.
    :return: the bytearray in which the game state is stored.
    """

    ba = bytearray()

    ba.extend(bytearray(BALL.x.to_bytes(2, signed=True)))
    ba.extend(bytearray(BALL.y.to_bytes(2, signed=True)))
    ba.extend(bytearray(BALL.size.to_bytes(2, signed=True)))
    ba.extend(bytearray(BALL.direction.to_bytes(2, signed=True)))
    ba.extend(bytearray(SCORE[0].to_bytes(2, signed=True)))
    ba.extend(bytearray(SCORE[1].to_bytes(2, signed=True)))
    ba.extend(bytearray(PADDLE_LEFT.x.to_bytes(2, signed=True)))
    ba.extend(bytearray(PADDLE_LEFT.y.to_bytes(2, signed=True)))
    ba.extend(bytearray(PADDLE_LEFT.width.to_bytes(2, signed=True)))
    ba.extend(bytearray(PADDLE_LEFT.height.to_bytes(2, signed=True)))
    ba.extend(bytearray(PADDLE_RIGHT.x.to_bytes(2, signed=True)))
    ba.extend(bytearray(PADDLE_RIGHT.y.to_bytes(2, signed=True)))
    ba.extend(bytearray(PADDLE_RIGHT.width.to_bytes(2, signed=True)))
    ba.extend(bytearray(PADDLE_RIGHT.height.to_bytes(2, signed=True)))
    # ba.extend(bytearray(CURRENT_PLAYERS.to_bytes(2, signed=True)))
    # ba.extend(bytearray(MAX_PLAYERS.to_bytes(2, signed=True)))

    return ba


if __name__ in {"__main__", "__main_mp__"}:
    socket_thread = threading.Thread(target=socket_things)
    socket_thread.start()

    pygame_run_function()
