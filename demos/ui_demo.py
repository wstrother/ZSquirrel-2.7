from game import Game
from app.pygame_screen import PygameScreen
from entities import Layer, Sprite
from context import Context
from ui.ui_interface import UiInterface, UiSprite, ContainerSprite
from ui.hud_interface import HudInterface


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
            UiInterface,
            HudInterface
        ]
    )

    c.load_environment("ui_demo.json")
    c.run_game()
