from game import Game
from app.pygame_screen import PygameScreen
from entities import Layer, Sprite
from context import Context
from animations.animation_interface import AnimationInterface
from control.controller_interface import ControllerInterface
import pygame


class SquirrelMachineInterface(AnimationInterface):
    @staticmethod
    def press_forward(sprite):
        if sprite.controller:
            dpad = sprite.controller.get_device("Dpad")
            x, y = dpad.get_value()

            return x == sprite.face_direction

    @staticmethod
    def press_back(sprite):
        if sprite.controller:
            dpad = sprite.controller.get_device("Dpad")
            x, y = dpad.get_value()

            return x == -1 * sprite.face_direction

    @staticmethod
    def press_direction(sprite):
        if sprite.controller:
            dpad = sprite.controller.get_device("Dpad")
            x, y = dpad.get_value()

            return x != 0

    @staticmethod
    def press_down(sprite):
        if sprite.controller:
            dpad = sprite.controller.get_device("Dpad")
            x, y = dpad.get_value()

            return y == 1

    @staticmethod
    def double_tap(sprite):
        if sprite.controller:
            commands = sprite.controller.commands
            left, right = commands["DT_LEFT"], commands["DT_RIGHT"]

            return left.active or right.active

    @staticmethod
    def auto(sprite):
        if sprite.graphics:
            return sprite.graphics.animation_cycles > 0


class GameSprite(Sprite):
    def __init__(self, name):
        super(GameSprite, self).__init__(name)

        self.face_direction = 1
        self.last_state = "default"

        self.update_methods.append(
            self.update_face_direction
        )

    def get_state(self):
        state = self.graphics.get_state()

        return state.replace("_left", "")

    def set_face_direction(self, value):
        self.face_direction = value

    def update_face_direction(self):
        if self.last_state == "pivot":
            frame = self.graphics.animation_meter.value
            cycle = self.graphics.animation_cycles

            if frame == 0 and cycle == 0:
                self.face_direction *= -1

    def on_change_state(self):
        e = self.event
        self.last_state = e["last_state"]


def main():
    clock = pygame.time.Clock()
    scr = PygameScreen((1100, 600))
    c = Context.get_default_context(
        Game(scr, clock=clock, frame_rate=60),
        [
            Sprite,
            GameSprite,
            Layer
        ],
        [
            SquirrelMachineInterface,
            ControllerInterface
        ]
    )

    c.load_environment("animations_demo.json")
    c.run_game()
