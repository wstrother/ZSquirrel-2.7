from context import Context, ApplicationInterface
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

    def update(self):
        super(ConTextEnv, self).update()

        for e in self.entities:
            e.update()


class DemoSprite:
    def __init__(self, name):
        self.name = name
        self.position = 0, 0

        self.update_methods = []

    @property
    def char(self):
        return self.name[0]

    def set_position(self, x, y):
        self.position = x, y

    def set_group(self, group):
        group.add_member(self)

    def update(self):
        for m in self.update_methods:
            m()


class FollowerInterface(ApplicationInterface):
    def follow_player(self, entity):
        player = self.get_value(PLAYER)
        entity.update_methods.append(
            lambda: FollowerInterface.update_position(entity, player)
        )

    @staticmethod
    def update_position(entity, target):
        x, y = entity.position
        tx, ty = target.position
        dx, dy = 0, 0

        if tx > x:
            dx = 1

        if tx < x:
            dx = -1

        if ty > y:
            dy = 1

        if ty < y:
            dy = -1

        x += dx
        y += dy
        entity.set_position(x, y)


def main():
    s = TextScreen((50, 12))
    c = Context.get_default_context(
        Game(s),
        {
            DemoSprite.__name__: DemoSprite,
            ConTextEnv.__name__: ConTextEnv
        },
        FollowerInterface
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
    # c.run_game()

    c.load_environment("context_demo.json")
    c.run_game()
