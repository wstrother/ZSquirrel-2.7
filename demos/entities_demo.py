import constants as con
from context import Context
from game import Game
from entities import Sprite, Layer
from demos.game_demo import TextScreen
from demos.context_demo import ContextDemoInterface


class TextGraphics:
    def __init__(self, entity):
        self.entity = entity

    def get_graphics(self, offset):
        e = self.entity
        char = e.name[0]

        x, y = e.position
        ox, oy = offset
        x += ox
        y += oy

        return [(char, x, y)]


class TextLayer(Layer):
    def on_player_death(self):
        print("\tGAME OVER")
        self.handle_event("death")

    def on_death(self):
        super(TextLayer, self).on_death()

        quit()


class TextSprite(Sprite):
    def __init__(self, name):
        super(TextSprite, self).__init__(name)

        self.graphics = TextGraphics(self)

    def on_sprite_collision(self):
        e = self.event
        other = e["other"]

        print("\t{}: Ouch, I ran into {}!".format(
            self.name, other.name
        ))

    def on_death(self):
        super(TextSprite, self).on_death()

        print("\t{}: I am dead now... :(".format(self.name))


class TextInterface(ContextDemoInterface):
    def follow_sprite_update(self, sprite, target):
        super(TextInterface, self).follow_sprite_update(sprite, target)

        if sprite.position == target.position:
            sprite.handle_event({
                con.NAME: "sprite_collision",
                "other": target
            })

            target.handle_event({
                con.NAME: "sprite_collision",
                "other": sprite
            })

    def collision_death(self, sprite):
        sprite.add_listener({
            con.NAME: "sprite_collision",
            con.RESPONSE: "death"
        })

        env = self.get_value(con.ENVIRONMENT)

        sprite.add_listener({
            con.NAME: "death",
            con.RESPONSE: "player_death",
            con.TARGET: env
        })


def main():
    s = TextScreen((50, 12))
    c = Context.get_default_context(
        Game(s),
        [
            TextSprite,
            TextLayer,
            Layer
        ],
        [
            TextInterface
        ]
    )

    c.load_environment("entities_demo.json")
    c.run_game()
