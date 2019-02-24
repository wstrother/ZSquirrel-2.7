from game import PygameScreen, Game
from context import Context, ApplicationInterface
from entities import Layer, Sprite
from control.controller_interface import ControllerInterface
import pygame


class TextInterface(ApplicationInterface):
    pass


class TextGraphics:
    def __init__(self, text):
        pass


def main():
    scr = PygameScreen((550, 300))
    c = Context.get_default_context(
        Game(scr),
        [
            Sprite,
            Layer
        ],
        [
            ControllerInterface
        ]
    )

    c.load_environment("controllers_demo.json")
    c.run_game()
