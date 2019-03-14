from demos.physics_demo import PhysicsSprite, StickDemoInterface, WallsInterface
from entities import Sprite, Layer
from game import Game
from context import Context
import pygame
from app.pygame_screen import PygameScreen
from ui.hud_interface import HudInterface
from ui.ui_interface import ContainerSprite
from physics.physics_interface import PhysicsInterface
from control.controller_interface import ControllerInterface
from cameras.cameras import CameraLayer


def main():
    clock = pygame.time.Clock()
    scr = PygameScreen((1100, 600))
    c = Context.get_default_context(
        Game(scr, clock=clock, frame_rate=60),
        [
            Sprite,
            PhysicsSprite,
            ContainerSprite,
            Layer,
            CameraLayer
        ],
        [
            StickDemoInterface,
            ControllerInterface,
            PhysicsInterface,
            WallsInterface,
            HudInterface
        ]
    )

    c.load_environment("cameras_demo.json")
    c.run_game()
