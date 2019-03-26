import pygame
from app.pygame_screen import PygameScreen
from context import Context
from game import Game
from entities import Sprite, Layer
from control.controller_interface import ControllerInterface
from ui.menus_interface import MenusInterface, BlockSprite


def main():
    clock = pygame.time.Clock()
    scr = PygameScreen((1100, 600))
    c = Context.get_default_context(
        Game(scr, clock=clock, frame_rate=60),
        [
            Sprite,
            Layer,
            BlockSprite
        ],
        [
            ControllerInterface,
            MenusInterface
        ]
    )

    c.load_environment("menus_demo.json")
    c.run_game()
