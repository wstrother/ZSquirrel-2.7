from game import Game, PygameScreen
from entities import Layer, Sprite
from context import Context
from geometry import Rect
from graphics import GraphicsInterface, GeometryGraphics
from control.controller_interface import ControllerInterface
from demos.animations_demo import GameSprite, SquirrelMachineInterface
from geometry import Wall, Vector
from physics.physics import Physics
from physics.physics_interface import PhysicsInterface
from ui.hud_interface import HudInterface
from ui.ui_interface import ContainerSprite
import pygame


class WallsInterface(GraphicsInterface):
    def __init__(self, *args):
        super(WallsInterface, self).__init__(*args)

        self.init_order += [
            self.set_walls.__name__,
            self.set_sprite_rects.__name__
        ]

    def set_walls(self, layer, group, *walls):
        layer.graphics = GeometryGraphics(layer)

        for wall in walls:
            start, end, color = wall
            group.add_member(
                Wall(start, end)
            )

        def add_walls(l):
            i = 0

            for w in walls:
                vector = group[i]
                c = w[2]
                l.graphics.items.append(
                    [vector, c]
                )
                i += 1

        layer.update_methods.append(layer.graphics.items.clear)
        layer.update_methods.append(
            lambda: add_walls(layer)
        )

    @staticmethod
    def set_sprite_rects(layer, group, color):
        def add_sprite_rects(g, l):
            for s in g:
                l.graphics.items.append(
                    [s.get_body_rect(), color]
                )

        layer.update_methods.append(
            lambda: add_sprite_rects(group, layer)
        )


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
        self.physics = Physics(self, 2, .65, .1, .2)
        self.update_methods += [
            self.physics.update,
            self.update_position,
            self.update_forces
        ]

        self.ground_vector = None

    def set_physics(self, m, g, e, f):
        self.set_mass(m)
        self.set_gravity(g)
        self.set_elasticity(e)
        self.set_friction(f)

    def get_velocity(self):
        return self.physics.velocity

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

        self.set_position(x, y)

        if self.ground_vector:
            self.physics.grounded = True

    def update_forces(self):
        stick = self.controller.get_device("Stick")
        x, y = stick.get_value()
        a = self.controller.get_device("A")
        movement = Vector(0, 0)
        grounded = self.physics.grounded

        state = self.get_state()
        direction = self.face_direction
        frame = self.graphics.animation_meter.value
        cycle = self.graphics.animation_cycles
        friction = self.physics.friction
        velocity = self.physics.velocity

        dx, dy = 0, 0

        if state == "walk":
            dx = 8 * friction * abs(x)

        if state == "dash":
            dx = 20 * friction * abs(x)

            if frame == 0:
                velocity.i_hat = 0
                dx *= 1.5

        if state == "run":
            dx = 16 * friction

        if state == "jump_squat":
            if self.last_state == "walk":
                dx = 8 * friction * abs(x)
            if self.last_state == "dash":
                dx = 20 * friction * abs(x)
            if self.last_state == "run":
                dx = 16 * friction

        if grounded:
            dx *= direction

        if state == "air_dodge":
            if frame <= 2:
                velocity.scale(0)

            if frame == 2:
                dy = y * 13
                dx = x * 14

            if frame < 16 and not self.physics.grounded:
                self.physics.gravity = self.default_g * .25
            else:
                self.physics.gravity = self.default_g

        if state == "jump_up":
            if frame == 0 and cycle == 0:
                self.physics.grounded = False
                if a.held:
                    dy = -35
                else:
                    dy = -24

        if state == "fast_fall":
            if frame == 0 and cycle == 0:
                dy += 10

        if state in ("jump_up", "jump_apex", "jump_fall", "fast_fall"):
            dx = x * .75
            velocity.i_hat *= .95

        if state == "special_fall":
            if frame == 0:
                velocity.scale_in_direction(0, .55)

        movement.set_value(dx, dy)
        movement.scale(1.4)

        if self.ground_vector:
            movement.rotate(self.ground_vector.get_angle())
            self.ground_vector = None

        self.physics.apply_force(*movement.get_value())

    def get_body_rect(self):
        r = self.graphics.animations[
            self.graphics.get_state()
        ].data["body"]
        rect = Rect(r["size"], r["position"])
        rect.move(self.position)

        return rect

    def get_collision_points(self):
        r = self.get_body_rect()

        return (
            r.topright, r.topleft,
            r.center,
            r.bottomright, r.bottomleft
        )

    def get_collision_skeleton(self):
        rect = self.get_body_rect()

        mt = rect.midtop
        mb = rect.midbottom
        ml = rect.midleft
        mr = rect.midright

        h = Wall(ml, mr)
        v = Wall(mt, mb)

        return h, v

    def on_vector_collision(self):
        e = self.event
        v = e["vector"]
        self.ground_vector = v


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
            PhysicsInterface,
            WallsInterface,
            HudInterface
        ]
    )

    c.load_environment("physics_demo.json")
    c.run_game()
