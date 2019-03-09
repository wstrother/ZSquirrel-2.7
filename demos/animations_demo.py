from game import Game, PygameScreen
from entities import Layer, Sprite
from context import Context
from animations.animation_interface import AnimationInterface
from control.controller_interface import ControllerInterface


class SquirrelMachineInterface(AnimationInterface):
    @staticmethod
    def press_direction(sprite):
        if sprite.controller:
            dpad = sprite.controller.get_device("Dpad")
            x, y = dpad.get_value()

            return x != 0

    @staticmethod
    def double_tap(sprite):
        if sprite.controller:
            commands = sprite.controller.commands
            left, right = commands["DT_LEFT"], commands["DT_RIGHT"]

            if left.active or right.active:
                return True


def main():
    scr = PygameScreen((1100, 600))
    c = Context.get_default_context(
        Game(scr),
        [
            Sprite,
            Layer
        ],
        [
            SquirrelMachineInterface,
            ControllerInterface
        ]
    )

    c.load_environment("animations_demo.json")
    c.run_game()
