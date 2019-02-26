from game import Game, PygameScreen
from entities import Layer, Sprite
from context import Context
from ui.ui_interface import UiInterface, UiSprite, ContainerSprite


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
            UiInterface
        ]
    )

    c.load_environment("ui_demo.json")
    c.run_game()
