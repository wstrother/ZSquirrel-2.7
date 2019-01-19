from context import Context
from game import Game
from demos.game_demo import TextEnv, TextScreen
import constants as con

PLAYER = "Player"


class ConTextEnv(TextEnv):
    def move_player(self, dx, dy):
        for e in self.entities:
            if e.name == PLAYER:
                x, y = e.position
                x += dx
                y += dy
                e.set_position(x, y)

    def get_graphics(self):
        args = []

        for e in self.entities:
            x, y = e.position
            char = e.char

            args.append((char, x, y))

        return args


class DemoPlayer:
    def __init__(self, name):
        self.name = name

        self.position = 0, 0
        self.char = ""

    def set_char(self, char):
        self.char = char

    def set_position(self, x, y):
        self.position = x, y


if __name__ == "__main__":
    s = TextScreen((50, 12))
    c = Context.get_default_context(
        Game(s), cd={
            DemoPlayer.__name__: DemoPlayer
        }
    )

    player = {
        con.CLASS: DemoPlayer.__name__,
        con.NAME: PLAYER,
        con.POSITION: (0, 0)
    }

    c.load_environment({
        con.SPRITES: [player]
    })

    c.run_game()
