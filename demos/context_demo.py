from context import Context
from game import Game
from demos.game_demo import TextEnv, TextScreen
import constants as con

PLAYER = "Player"
SPRITE_GROUP = "sprite_group"


class ConTextEnv(TextEnv):
    def __init__(self, *args, **kwargs):
        super(ConTextEnv, self).__init__(*args, **kwargs)
        self.groups = []

    @property
    def entities(self):
        entities = []
        for g in self.groups:
            entities += g

        return entities

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

    def set_groups(self, *groups):
        self.groups += groups


class DemoPlayer:
    def __init__(self, name):
        self.name = name

        self.position = 0, 0

    @property
    def char(self):
        return self.name[0]

    def set_position(self, x, y):
        self.position = x, y

    def set_group(self, group):
        group.add_member(self)


if __name__ == "demos.context_demo":
    s = TextScreen((50, 12))
    c = Context.get_default_context(
        Game(s), cd={
            DemoPlayer.__name__: DemoPlayer,
            ConTextEnv.__name__: ConTextEnv
        }
    )

    # player = {
    #     con.CLASS: DemoPlayer.__name__,
    #     con.NAME: PLAYER,
    #     con.POSITION: [5, 1],
    #     con.GROUP: SPRITE_GROUP
    # }
    #
    # env = {
    #     con.CLASS: ConTextEnv.__name__,
    #     con.NAME: con.ENVIRONMENT,
    #     con.GROUPS: SPRITE_GROUP
    # }
    #
    # c.load_environment({
    #     con.SPRITES: [player],
    #     con.LAYERS: [env]
    # })

    c.load_environment("context_demo." + con.JSON)
    c.run_game()
