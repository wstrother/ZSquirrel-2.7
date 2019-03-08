from game import PygameScreen, Game
from context import Context, ApplicationInterface
from entities import Layer, Sprite
from control.controller_interface import ControllerInterface
from control.command_inputs import CommandInput, CommandStep, CommandCondition
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

    def set_command_input_hud(self, sprite, devices, name, window, *steps):
        command = CommandInput(name, devices, window, *steps)
        hud_sprite = HudSprite(name + "  hud", 30, 6)
        self.set_text(hud_sprite, "")

        sprite.update_methods.append(
            lambda: command.update(
                sprite.controller.get_command_frames(devices, 1)
            )
        )

        hud_sprite.set_value_func(
            self.get_attr_func(command, "active")
        )
        hud_sprite.get_cache = lambda: hud_sprite.get_cache_changes(2)

        self.set_member_sprites(sprite, [[hud_sprite]])

    def set_command_step_hud(self, sprite, devices, name, window, *conditions):
        step = CommandStep(name, window, *conditions)
        self.context.set_value(name, step)

        hud_sprite = HudSprite(name + " hud", 1, 1)
        self.set_text(hud_sprite, "")
        hud_sprite.set_value_func(
            lambda: step.check(
                sprite.controller.get_command_frames(devices, window)
            )
        )

        table = [[
            self.get_item_as_sprite(name),
            hud_sprite
        ]]
        self.set_member_sprites(sprite, *table)

    def add_command_condition(self, name, *args):
        args = list(args)
        for arg in args:
            if type(arg) is str:
                args[args.index(arg)] = self.get_value(arg)

        condition = CommandCondition(*args)
        self.context.set_value(name, condition)

        return condition

    def set_conditions_hud(self, sprite, devices, *conditions):
        table = []
        for c in conditions:
            name, *args = c
            condition = self.add_command_condition(name, *args)
            table.append(
                [
                    self.get_item_as_sprite(name),
                    self.get_condition_hud(name, condition, sprite, devices)
                ]
            )

        self.set_member_sprites(sprite, *table)

    def get_condition_hud(self, name, condition, sprite, devices):
        hud_sprite = HudSprite(name + " hud", 1, 1)
        self.set_text(hud_sprite, "")
        hud_sprite.set_value_func(
            lambda: condition.check(
                self.get_command_frames(sprite, devices)
            )
        )

        return hud_sprite

    @staticmethod
    def get_command_frames(sprite, devices):
        controller = sprite.controller
        inputs = []

        for name in devices:
            device = controller.get_device(name)
            frames = device.get_frames()
            if not frames:
                value = device.default
            else:
                value = frames[-1]

            if type(value) is tuple:
                inputs += list(value)
            else:
                inputs.append(value)

        return inputs


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
