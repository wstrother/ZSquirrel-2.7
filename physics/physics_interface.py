from context import ApplicationInterface
from geometry import Vector, add_points
from entities import Group
from physics.physics import CollisionSystem


class PhysicsInterface(ApplicationInterface):
    def set_collision_system(self, layer, test, handle, *groups):
        test = self.get_collision_method(test)
        handle = self.get_collision_method(handle)

        groups = list(groups)
        for g in groups:
            if type(g) is str:
                name = g
                group = Group(name)

                self.context.set_value(name, group)
                groups[groups.index(g)] = group

        cs = self.get_collision_system(test, handle, *groups)

        layer.update_methods.append(cs.update)

    def get_collision_method(self, method):
        if type(method) is str:
            return getattr(self, method)

        else:
            return method

    @staticmethod
    def get_collision_system(test, handle, *groups):
        a = groups[0]
        b = None
        if len(groups) > 1:
            b = groups[1]
        return CollisionSystem(
            a, b, test, handle
        )

    @staticmethod
    def wall_velocity_test(wall, sprite):
        n = wall.get_normal()
        n.rotate(.5)

        points = sprite.get_collision_points()
        v = sprite.get_velocity()

        if n.check_orientation(v):
            for point in points:
                collision = wall.vector_collision(v, point)

                if collision:
                    return point

    @staticmethod
    def test_wall_collision(wall, sprite):
        s_test = PhysicsInterface.wall_skeleton_test(wall, sprite)

        if s_test:
            return s_test

        else:
            v_test = PhysicsInterface.wall_velocity_test(wall, sprite)

            return v_test

    @staticmethod
    def wall_skeleton_test(wall, sprite):
        v = sprite.get_velocity()
        n = wall.get_normal()

        if not n.check_orientation(v):
            skeleton = sprite.get_collision_skeleton()
            angle = n.get_angle() + .5
            angle -= angle // 1

            r = (0 <= angle < .125) or (.875 <= angle <= 1)
            t = .125 <= angle < .375
            l = .375 <= angle < .675
            b = .675 <= angle < .875

            h = l or r
            v = t or b

            if h:
                w = skeleton[0]
                collision = wall.vector_collision(w, w.origin)

                if collision:
                    if l:
                        return w.origin

                    if r:
                        return w.end_point
            if v:
                w = skeleton[1]
                collision = wall.vector_collision(w, w.origin)

                if collision:
                    if t:
                        return w.origin

                    if b:
                        return w.end_point

    @staticmethod
    def smooth_wall_collision(wall, sprite, point):
        v = sprite.get_velocity()

        projected = v.apply_to_point(point)
        adjustment = wall.get_normal_adjustment(
            projected
        )
        adjustment = add_points(adjustment, v.get_value())
        sprite.move(*adjustment)

        normal = wall.get_normal()
        sprite.physics.scale_movement_in_direction(
            normal.get_angle(), 0)

        sprite.handle_event({
            "name": "vector_collision",
            "vector": wall
        })

    @staticmethod
    def bounce_wall_collision(wall, sprite, point):
        v = sprite.get_velocity()

        sprite.physics.apply_force(
            *wall.get_normal_adjustment(
                v.apply_to_point(point)
            )
        )

        normal = wall.get_normal()
        v.scale_in_direction(
            normal.get_angle() + .25, 0
        )
        v.scale(.5)
        sprite.move(*v.get_value())

        sprite.physics.scale_movement_in_direction(
            normal.get_angle(), -1)

    @staticmethod
    def sprite_sprite_collision(s1, s2):
        r1 = s1.get_animation_rect("body")
        r2 = s2.get_animation_rect("body")

        return r1.get_rect_collision(r2)

    @staticmethod
    def handle_sprite_collision(sprite, other, collision):
        if collision:
            def check_orientation(s):
                x, y = s.get_center_of_mass()
                cx, cy = collision
                heading = Vector(cx - x, cy - y)

                return s.get_velocity().check_orientation(heading)

            def get_adjustment(o):
                x, y = o.get_center_of_mass()
                cx, cy = collision
                v = Vector(cx - x, cy - y)

                return v

            def do_adjustment(s, o):
                v = get_adjustment(o)

                if check_orientation(s):
                    s.physics.scale_movement_in_direction(v.get_angle(), 0)

                v.scale(1 - s.physics.elasticity)
                s.physics.apply_force(*v.get_value())

            do_adjustment(sprite, other)
            do_adjustment(other, sprite)
