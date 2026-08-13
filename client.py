# Standard imports
import time

# Extra imports
from server import *

speed = 5

pg.init()
pg.display.set_caption("Pong Online")

w, h = SCREEN_WIDTH, SCREEN_HEIGHT
screen = pg.display.set_mode((w, h), *SCREEN_OPTIONS)
clock = pg.time.Clock()

score = [0, 0]
game_over = False
go_text = pg.font.Font(None, 102)
s_text = pg.font.Font(None, 52)

# Screen borders
top = lambda: (0, 0, w, 0)
bottom = lambda: (0, h - 1, w, h - 1)
left = lambda: (0, 0, 0, h)
right = lambda: (w - 1, 0, w - 1, h)

sides = [top, bottom, left, right]

# Paddle borders
paddle_top = lambda: (our_paddle.x, our_paddle.y, our_paddle.x + our_paddle.width, our_paddle.y)
paddle_bottom = lambda: (our_paddle.x, our_paddle.y + our_paddle.height - 1, our_paddle.x + our_paddle.width - 1,
                         our_paddle.y + our_paddle.height - 1)
paddle_right = lambda: (our_paddle.x + our_paddle.width, our_paddle.y, our_paddle.x + our_paddle.width,
                        our_paddle.y + our_paddle.height)

paddle_sides = [paddle_top, paddle_bottom, paddle_right]

send = bytearray(2)


def draw_State(__json_encoded_state, /):
    with json.loads(__json_encoded_state) as state:
        # Ball Statistics
        _ball.x = state['BX']
        _ball.y = state['BY']
        _ball.size = state['BSZ']
        _ball.direction = state['BD']

        # Left Paddle Statistics
        left_paddle.x = state['LPX']
        left_paddle.y = state['LPY']
        left_paddle.width = state['LPW']
        left_paddle.height = state['LPH']

        # Right Paddle Statistics
        right_paddle.x = state['RPX']
        right_paddle.y = state['RPY']
        right_paddle.width = state['RPW']
        right_paddle.height = state['RPH']

    return state


class section:
    @staticmethod
    def function(score, *objs: object, screen=None):
        """
        Draw every object with obj.draw()
        If an exception occurs, continue drawing.
        :param score:
        :param screen: screen on which to draw on.
        :param objs: the list of objects to be drawn
        """

        for obj in objs:
            if obj:
                obj.draw(screen)
        if score:
            score_text = s_text.render(f'{score[0]} | {score[1]}', True, "blue")
            screen.blit(score_text, ((screen.get_width() / 2) - (score_text.get_width() / 2), 25))


# REGEXPS

runningx = True
side = sys.argv[3]
our_paddle = None
left_paddle = None
right_paddle = None
_ball = None
game_state: dict[str, Any]
counter = 0

draw_frame = section.function


def pg_thread():
    global score, runningx, game_state, send, counter

    while runningx:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                send = 'Q'.encode('ascii')
                runningx = False
                screen.fill((0, 0, 0))

                continue

        screen.fill((0, 0, 0))
        draw_frame(score, left_paddle, right_paddle, _ball, screen=screen)
        pg.display.flip()

        key = pg.key.get_pressed()

        if our_paddle and our_paddle.side:
            if key[pg.K_UP] or key[pg.K_w]:
                send_paddle_position(-speed, our_paddle.side)

            if key[pg.K_DOWN] or key[pg.K_s]:
                send_paddle_position(speed, our_paddle.side)

        clock.tick(60)


# def socket_send_thread():
#     global send, runningx
#     with (socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s):
#         s.connect((sys.argv[1], int(sys.argv[2])))
#         s.settimeout(15.0)
#
#         if len(send) > 0:
#             s.send(send)
#             send = b""


def socket_recv_thread():
    global send, runningx
    gs = 'GS'.encode('ascii')
    global our_paddle, left_paddle, right_paddle, _ball, score, side, counter
    with (socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s):
        s.connect((sys.argv[1], int(sys.argv[2])))
        s.settimeout(0)

        start = time.time_ns()
        ns_between_frames = (1/30) * 1e9

        while runningx:
            ct = time.time_ns()
            if send[1] != 0:
                s.send(send)
                send[1] = 0

            if (ct - start) > ns_between_frames:
                start = ct

                s.send(gs)

                # start
                try:
                    # data = bytearray()
                    # while True:
                    #     packet = s.recv(1024)
                    #     if not packet:
                    #         break
                    #     data.extend(packet)
                    #     try:
                    #         game_state = json.loads(data)
                    #         break
                    #     except:
                    #         pass
                    # #end2
                    data = bytearray(s.recv(28))
                    game_state = decode_game_state(data)
                    score[0] = game_state['SCR0']
                    score[1] = game_state['SCR1']

                    if _ball is None:
                        _ball = ball.Ball(0, 0, 0, 0)
                        _ball.size = game_state['BSZ']

                    if left_paddle is None:
                        left_paddle = paddle.Paddle(0, 0, 0, 0, 0, side='L')
                        left_paddle.width = game_state['LPW']
                        left_paddle.height = game_state['LPH']

                        if side == 'L':
                            our_paddle = left_paddle

                    if right_paddle is None:
                        right_paddle = paddle.Paddle(0, 0, 0, 0, 0, side='R')
                        right_paddle.width = game_state['RPW']
                        right_paddle.height = game_state['RPH']

                        if side == 'R':
                            our_paddle = right_paddle

                    _ball.x = game_state['BX']
                    _ball.y = game_state['BY']

                    left_paddle.x = game_state['LPX']
                    left_paddle.y = game_state['LPY']

                    right_paddle.x = game_state['RPX']
                    right_paddle.y = game_state['RPY']

                except BaseException as e:
                    pass
                    #print("error", e)


def send_paddle_position(change, side):
    global send

    send[0] = ord(side)
    send[1:2] = int.to_bytes(change, 1, signed=True)


if __name__ == "__main__":
    print(sys.argv)
    #threading.Thread(target=socket_send_thread).start()
    threading.Thread(target=socket_recv_thread).start()
    pg_thread()
