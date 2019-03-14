from game import Game
from app.pygame_screen import PygameScreen
from entities import Layer, Sprite
from context import Context
from graphics import GraphicsInterface


def main():
    scr = PygameScreen((1100, 600))
    c = Context.get_default_context(
        Game(scr),
        [
            Sprite,
            Layer
        ],
        [
            GraphicsInterface
        ]
    )

    c.load_environment("graphics_demo.json")
    c.run_game()
