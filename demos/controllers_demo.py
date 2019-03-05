from game import PygameScreen, Game
from context import Context, ApplicationInterface
from entities import Layer, Sprite
from control.controller_interface import ControllerInterface
from graphics import GraphicsInterface
from ui.ui_interface import UiInterface, UiSprite, ContainerSprite
from ui.hud_interface import HudInterface


class ContDemoInterface(ApplicationInterface):
    @staticmethod
    def move_sprite(sprite, v):
        sprite.update_methods.append(
            lambda: dpad_movement(sprite, v)
        )


def dpad_movement(sprite, v):
    if sprite.controller:
        dpad = sprite.controller.get_device("Dpad")
        dx, dy = dpad.get_value()

        sprite.move(dx, dy, v)


def main():
    scr = PygameScreen((1100, 600))
    c = Context.get_default_context(
        Game(scr),
        [
            Sprite,
            UiSprite,
            ContainerSprite,
            Layer
        ],
        [
            GraphicsInterface,
            UiInterface,
            HudInterface,
            ControllerInterface,
            ContDemoInterface
        ]
    )

    c.load_environment("controllers_demo.json")
    c.run_game()
