from context import Context, ApplicationInterface
from game import Game
from demos.game_demo import TextEnv, TextScreen

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
        if self.updated:
            for e in self.entities:
                e.update()

                if not e.spawned:
                    e.spawned = True

        self.updated = True


class DemoSprite:
    def __init__(self, name):
        self.name = name
        self.spawned = False
        self.dead = False
        self.position = 0, 0

        self.update_methods = []

    def move(self, dx, dy):
        x, y = self.position
        self.set_position(x + dx, y + dy)

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


class ContextDemoInterface(ApplicationInterface):
    def follow_player(self, sprite):
        target = self.get_value(PLAYER)
        self.follow_sprite(sprite, target)

    def follow_sprite(self, sprite, target):
        sprite.update_methods.append(
            lambda: self.follow_sprite_update(sprite, target)
        )

    def text_movement(self, sprite):
        sprite.update_methods.append(
            lambda: self.get_text_input(sprite)
        )

    @staticmethod
    def follow_sprite_update(sprite, target):
        if sprite.spawned:
            x, y = sprite.position
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
            sprite.set_position(x, y)

    @staticmethod
    def get_text_input(sprite):
        if sprite.spawned and not sprite.dead:
            text = input("Input for {} > ".format(sprite.name))

            if "q" in text:
                exit()

            x, y = 0, 0
            up = "u" in text
            down = "d" in text
            left = "l" in text
            right = "r" in text

            if up:
                y -= 1
            if down:
                y += 1
            if left:
                x -= 1
            if right:
                x += 1

            sprite.move(x, y)


def main():
    s = TextScreen((50, 12))
    c = Context.get_default_context(
        Game(s),
        [
            DemoSprite,
            ConTextEnv
        ],
        [
            ContextDemoInterface
        ]
    )

    c.load_environment("context_demo.json")
    c.run_game()
