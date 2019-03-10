from geometry import Vector


class Physics:
    def __init__(self, entity, mass, gravity, elasticity, friction):
        self.entity = entity

        self.mass = mass
        self.gravity = gravity

        self.grounded = False
        self.elasticity = elasticity
        self.friction = friction

        self.velocity = Vector(0, 0)
        self.forces = []
        self.last_position = 0, 0

    def get_instantaneous_velocity(self):
        entity = self.entity
        x, y = entity.position
        lx, ly = self.last_position

        x -= lx
        y -= ly

        return Vector(x, y)

    def set_mass(self, value):
        self.mass = value

    def set_elasticity(self, value):
        self.elasticity = value

    def set_gravity(self, value):
        self.gravity = value

    def set_friction(self, value):
        self.friction = value

    def scale_movement_in_direction(self, angle, value):
        self.velocity.scale_in_direction(angle, value)

    def apply_force(self, i, j):
        self.forces.append(
            Vector(i, j)
        )

    def integrate_forces(self):
        forces = self.forces
        self.forces = []

        i, j = 0, 0

        for f in forces:
            i += f.i_hat
            j += f.j_hat

        acceleration = Vector(i, j).scale(1 / self.mass)
        self.velocity.add_vector(acceleration)

    def apply_velocity(self):
        self.entity.move(
            *self.velocity.get_value()
        )

    def update(self):
        self.last_position = self.entity.position

        # gravity
        if self.gravity:
            g = self.gravity * self.mass
            self.apply_force(0, g)

        self.integrate_forces()

        # movement
        if self.grounded and self.gravity:
            self.velocity.scale(1 - self.friction)

        self.apply_velocity()
