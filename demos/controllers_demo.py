from game import Game
from app.pygame_screen import PygameScreen
from context import Context
from entities import Layer, Sprite
from control.controller_interface import ControllerInterface
from graphics import GraphicsInterface
from ui.ui_interface import UiInterface, UiSprite, ContainerSprite
from ui.hud_interface import HudInterface, HudSprite
import pygame


class ContDemoInterface(HudInterface):
    def move_sprite(self, sprite, v):
        sprite.update_methods.append(
            lambda: self.dpad_movement(sprite, v)
        )

    @staticmethod
    def dpad_movement(sprite, v):
        if sprite.controller:
            dpad = sprite.controller.get_device("Dpad")
            dx, dy = dpad.get_value()

            sprite.move(dx, dy, v)

    def set_command_hud(self, sprite, *commands):
        self.set_container_image(sprite)
        table = []

        for c in commands:
            hud_sprite = HudSprite(c.name + " hud", 30, 30)
            self.set_text(hud_sprite, "")
            hud_sprite.set_value_func(
                self.get_command_hud_func(c)
            )
            hud_sprite.set_cache_func(hud_sprite.get_cache_change_func(1))

            table.append([hud_sprite])

        self.set_member_sprites(sprite, *table)

    @staticmethod
    def get_command_hud_func(command):
        def value_func():
            if command.active:
                return command.name

        return value_func


def main():
    scr = PygameScreen((1100, 600))
    clock = pygame.time.Clock()

    c = Context.get_default_context(
        Game(scr, clock=clock, frame_rate=60),
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
