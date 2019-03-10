from game import Game, PygameScreen
from entities import Layer, Sprite
from context import Context
from control.controller_interface import ControllerInterface
from demos.animations_demo import GameSprite, SquirrelMachineInterface
from physics.physics import Physics
from ui.hud_interface import HudInterface
from ui.ui_interface import ContainerSprite
import pygame


class StickDemoInterface(SquirrelMachineInterface):
    @staticmethod
    def press_forward(sprite):
        if sprite.controller:
            stick = sprite.controller.get_device("Stick")
            x, y = stick.get_value()

            if abs(x) > .2:
                stick_p = x > 0
                face_p = sprite.face_direction > 0

                return stick_p == face_p

    @staticmethod
    def full_forward(sprite):
        if sprite.controller:
            stick = sprite.controller.get_device("Stick")
            x, y = stick.get_value()

            if abs(x) > .95:
                stick_p = x > 0
                face_p = sprite.face_direction > 0

                return stick_p == face_p

    @staticmethod
    def tap_down(sprite):
        if sprite.controller:
            commands = sprite.controller.commands
            down = commands["DT_DOWN"]

            return down.active

    @staticmethod
    def press_back(sprite):
        if sprite.controller:
            stick = sprite.controller.get_device("Stick")
            x, y = stick.get_value()

            if abs(x) > .5:
                stick_p = x > 0
                face_p = sprite.face_direction > 0

                return stick_p != face_p

    @staticmethod
    def press_direction(sprite):
        if sprite.controller:
            stick = sprite.controller.get_device("Stick")
            x, y = stick.get_value()

            return abs(x) > .1

    @staticmethod
    def press_down(sprite):
        if sprite.controller:
            stick = sprite.controller.get_device("Stick")
            x, y = stick.get_value()

            return y > .1

    @staticmethod
    def press_jump(sprite):
        if sprite.controller:
            return sprite.controller.get_device("A").held == 1

    @staticmethod
    def press_dodge(sprite):
        if sprite.controller:
            return sprite.controller.get_device("Z").held == 1

    @staticmethod
    def in_air(sprite):
        if sprite.physics:
            return not sprite.physics.grounded

    @staticmethod
    def ground_collision(sprite):
        if sprite.physics:
            return sprite.physics.grounded

    @staticmethod
    def peak_jump(sprite):
        if sprite.physics:
            cycles = sprite.graphics.animation_cycles
            j = sprite.physics.velocity.j_hat

            return j >= 0 and cycles > 1


class PhysicsSprite(GameSprite):
    def __init__(self, name):
        super(PhysicsSprite, self).__init__(name)

        self.default_g = .65
        self.physics = Physics(self, 1, .65, .1, .15)
        self.update_methods += [
            self.physics.update,
            self.update_position,
            self.update_forces
        ]

    def set_physics(self, m, g, e, f):
        self.set_mass(m)
        self.set_gravity(g)
        self.set_elasticity(e)
        self.set_friction(f)

    def set_mass(self, value):
        self.physics.mass = value

    def set_gravity(self, g):
        self.physics.gravity = g

    def set_friction(self, f):
        self.physics.friction = f

    def set_elasticity(self, e):
        self.physics.elasticity = e

    def update_position(self):
        x, y = self.position
        w, h = self.size
        self.physics.grounded = False

        if x > 1100:
            x -= 1100

        if x < -w:
            x += (1100 + w)

        if y > 600:
            self.physics.grounded = True
            y = 600

        self.set_position(x, y)

    def update_forces(self):
        stick = self.controller.get_device("Stick")
        x, y = stick.get_value()
        a = self.controller.get_device("A")

        state = self.get_state()
        direction = self.face_direction
        frame = self.graphics.animation_meter.value
        cycle = self.graphics.animation_cycles
        friction = self.physics.friction
        velocity = self.physics.velocity

        dx, dy = 0, 0

        if state == "walk":
            dx = 10 * friction * abs(x)

        if state == "dash":
            dx = 25 * friction * abs(x)

            if frame == 0:
                velocity.i_hat = 0
                dx *= 1.5

        if state == "run":
            dx = 20 * friction

        if state == "jump_squat":
            if self.last_state == "walk":
                dx = 10 * friction * abs(x)
            if self.last_state == "dash":
                dx = 25 * friction * abs(x)
            if self.last_state == "run":
                dx = 20 * friction

        dx *= direction

        if state == "air_dodge":
            if frame == 0:
                velocity.scale(0)

                dy = y * 7
                dx = x * 7

            if frame < 16 and not self.physics.grounded:
                self.physics.gravity = self.default_g / 2
            else:
                self.physics.gravity = self.default_g

        if state == "jump_up":
            if frame == 0 and cycle == 0:
                if a.held:
                    dy = -30
                else:
                    dy = -20

        if state == "fast_fall":
            if frame == 0 and cycle == 0:
                dy += 10

        if state in ("jump_up", "jump_apex", "jump_fall", "fast_fall"):
            dx = x * .75
            velocity.scale_in_direction(0, .95)

        if state == "special_fall":
            if frame == 0:
                velocity.scale_in_direction(0, .75)

        self.physics.apply_force(dx, dy)


def main():
    clock = pygame.time.Clock()
    scr = PygameScreen((1100, 600))
    c = Context.get_default_context(
        Game(scr, clock=clock, frame_rate=60),
        [
            Sprite,
            PhysicsSprite,
            ContainerSprite,
            Layer
        ],
        [
            StickDemoInterface,
            ControllerInterface,
            HudInterface
        ]
    )

    c.load_environment("physics_demo.json")
    c.run_game()
