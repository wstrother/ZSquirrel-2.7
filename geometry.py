import pygame
from math import sqrt, pi, cos, sin, atan2


def add_points(p1, p2, inverse=False):
    x1, y1 = p1
    x2, y2 = p2

    if inverse:
        x2 *= -1
        y2 *= -1

    return x1 + x2, y1 + y2


def get_distance(p1, p2):
    x1, y1 = p1
    x2, y2 = p2

    dx = abs(x1 - x2)
    dy = abs(y1 - y2)

    return sqrt(dx**2 + dy**2)


class Rect:
    def __init__(self, size, position):
        self.size = size
        self.position = position

        self.color = None

    def __repr__(self):
        return "Rect: {}, {}".format(self.size, self.position)

    def scale(self, scale, center=True):
        cx, cy = self.center
        w, h = self.size
        w *= scale
        h *= scale

        self.size = w, h

        if center:
            self.center = cx, cy

    def grow(self, dw, dh, center=True):
        cx, cy = self.center
        w, h = self.size
        w += dw
        h += dh

        self.size = w, h

        if center:
            self.center = cx, cy

    @staticmethod
    def get_from_diagonals(point_a, point_b):
        xa, ya = point_a
        xb, yb = point_b
        x = min(xa, xb)
        y = min(ya, yb)
        w = max(xa, xb) - x
        h = max(ya, yb) - y

        return Rect((w, h), (x, y))

    def move(self, value):
        dx, dy = value
        x, y = self.position
        x += dx
        y += dy
        self.position = x, y

    @property
    def pygame_rect(self):
        r = pygame.Rect(
            self.position, self.size
        )

        return r

    @property
    def clip(self):
        return self.pygame_rect.clip

    def copy(self):
        return self.get_from_pygame_rect(self.pygame_rect.copy())

    @staticmethod
    def get_from_pygame_rect(rect):
        return Rect(rect.size, rect.topleft)

    @property
    def width(self):
        return self.size[0]

    @width.setter
    def width(self, value):
        self.size = value, self.size[1]

    @property
    def height(self):
        return self.size[1]

    @height.setter
    def height(self, value):
        self.size = self.size[0], value

    @property
    def right(self):
        return self.position[0] + self.width

    @right.setter
    def right(self, value):
        dx = value - self.right
        self.move((dx, 0))

    @property
    def left(self):
        return self.position[0]

    @left.setter
    def left(self, value):
        dx = value - self.left
        self.move((dx, 0))

    @property
    def top(self):
        return self.position[1]

    @top.setter
    def top(self, value):
        dy = value - self.top
        self.move((0, dy))

    @property
    def bottom(self):
        return self.top + self.height

    @bottom.setter
    def bottom(self, value):
        dy = value - self.bottom
        self.move((0, dy))

    @property
    def midleft(self):
        return self.left, self.top + (self.height / 2)

    @property
    def topleft(self):
        return self.left, self.top

    @property
    def midtop(self):
        return self.left + (self.width / 2), self.top

    @property
    def topright(self):
        return self.right, self.top

    @property
    def midright(self):
        return self.right, self.top + (self.height / 2)

    @property
    def bottomleft(self):
        return self.left, self.bottom

    @property
    def midbottom(self):
        return self.left + (self.width / 2), self.bottom

    @property
    def bottomright(self):
        return self.right, self.bottom

    @property
    def center(self):
        return (self.left + (self.width / 2),
                self.top + (self.height / 2))

    @center.setter
    def center(self, value):
        x, y = value
        x -= self.width / 2
        y -= self.height / 2

        self.position = x, y

    @property
    def collision_points(self):
        return (
            self.topleft, self.topright,
            self.center,
            self.bottomleft, self.bottomright
        )

    def get_rect_collision(self, other):
        try:
            collision = self.clip(other.pygame_rect)

            if not (collision.width or collision.height):
                return False

            else:
                return collision.center

        except ValueError:
            return False

    def get_circle_collision(self, radius, position):
        px, py = position
        pl, pr = px - radius, px + radius
        pt, pb = py - radius, py + radius

        t, l, r, b = (
            self.top, self.left,
            self.right, self.bottom
        )

        x_bound = pr >= l and pl <= r
        y_bound = pb >= t and pt <= b

        return x_bound and y_bound

    def get_walls(self, invert=False):
        a, b, c, d = (
            self.topleft, self.topright,
            self.bottomright, self.bottomleft
        )

        if not invert:
            top = Wall(a, b)
            right = Wall(b, c)
            bottom = Wall(c, d)
            left = Wall(d, a)

        else:
            top = Wall(b, a)
            right = Wall(c, b)
            bottom = Wall(d, c)
            left = Wall(a, d)

        return (
            top, right, bottom, left
        )

    def get_diagonal_walls(self):
        tl, tr, bl, br = (
            self.topleft, self.topright,
            self.bottomleft, self.bottomright
        )
        w, x, y, z = (
            Wall(bl, tr),
            Wall(tl, br),
            Wall(tr, bl),
            Wall(br, tl)
        )

        return w, x, y, z

    def get_copy(self, move=None, scale=1):
        new = Rect(self.size, self.position)
        new.scale(scale)
        if move:
            new.move(move)

        return new

    def get_distance(self, point):
        if self.get_circle_collision(0, point):
            return 0

        else:
            skeleton = Wall(point, self.center)

            for w in self.get_walls():
                c = w.vector_collision(skeleton, skeleton.origin)

                if c:
                    return get_distance(point, c)


class Vector:
    def __init__(self, i_hat, j_hat):
        self.i_hat = i_hat
        self.j_hat = j_hat

        self.color = None

    def __repr__(self):
        i, j = self.get_value()

        return "Vector: {:.3f}i, {:.3f}j".format(i, j)

    def get_value(self):
        return self.i_hat, self.j_hat

    def get_magnitude(self):
        i, j = self.get_value()

        return sqrt(i ** 2 + j ** 2)

    def add_vector(self, vector):
        c = self.complex + vector.complex
        self.i_hat = c.real
        self.j_hat = c.imag

        return self

    def scale(self, scalar):
        self.i_hat *= scalar
        self.j_hat *= scalar

    def scale_in_direction(self, angle, scalar):
        i, j = self.get_basis_vectors(angle)
        m1 = Matrix.get_from_vectors(i, j)

        m2 = Matrix([
            [scalar, 0],
            [0, 1]
        ])
        m = Matrix(m2.multiply_matrix(m1))

        i, j = m.multiply_vector(self)
        self.i_hat = i
        self.j_hat = j
        self.rotate(angle)

    @staticmethod
    def get_basis_vectors(angle):
        angle *= -1
        i = Vector(1, 0).rotate(angle)
        j = Vector(0, 1).rotate(angle)

        return i, j

    def multiply(self, vector):
        c = self.complex * vector.complex
        self.i_hat = c.real
        self.j_hat = c.imag

        return self

    # Returns the vector's angle in Tau * Radians
    def get_angle(self):
        i, j = self.get_value()
        angle = atan2(-j, i) / (2 * pi)  # NOTE: Multiply j value by -1 because down is positive

        if angle >= 0:
            theta = angle

        else:
            theta = 1 + angle

        return theta

    def get_quadrant(self):
        theta = self.get_angle()

        if 0 <= theta < .25:
            return 1

        if .25 <= theta < .5:
            return 2

        if .5 <= theta < .75:
            return 3

        if .75 <= theta <= 1:
            return 4

        else:
            raise ValueError("angle {}".format(theta))

    # Alters vector values in place to make its angle match a given value in Tau * Radians
    def set_angle(self, angle):
        theta = self.get_angle()
        delta = angle - theta
        self.rotate(delta)

    # Alters vector values in place to rotate its angle by a given Tau * Radians value
    def rotate(self, theta):
        theta *= (2 * pi)
        i, j = cos(theta), sin(theta)

        self.multiply(Vector(i, -j))

        return self

    # Returns the vector's displacement values applied to a point.
    def apply_to_point(self, point=(0, 0)):
        x, y = point
        x += self.i_hat
        y += self.j_hat

        return x, y

    def get_copy(self, rotate=0.0, scale=1):
        v = Vector(self.i_hat, self.j_hat)

        if rotate:
            v.rotate(rotate)

        v.scale(scale)

        return v

    # Alter vector values in place
    def set_value(self, i_hat, j_hat):
        self.i_hat = i_hat
        self.j_hat = j_hat

    @staticmethod
    def get_from_complex(c):
        i, j = c.real, c.imag

        return Vector(i, j)

    @property
    def complex(self):
        return complex(self.i_hat, self.j_hat)

    @property
    def magnitude(self):
        return abs(self.complex)

    # Returns False if the angle is vertical.
    def get_y_intercept(self, origin):
        if self.i_hat == 0:  # no Y-intercept for vertical lines
            return False

        if self.j_hat == 0:
            return origin[1]  # horizontal line just returns y value

        slope = self.j_hat / self.i_hat
        x0, y0 = origin

        c = y0 - (slope * x0)

        return c

    def check_orientation(self, vector):
        t1, t2 = self.get_angle(), vector.get_angle()

        def compare_angles(a1, a2):
            top = a1 + .25
            bottom = a1 - .25

            return bottom < a2 < top

        if .25 <= t1 < .75:
            return compare_angles(t1, t2)

        elif t1 < .25:
            return compare_angles(
                t1 + .25, (t2 + .25) % 1)

        elif .75 <= t1:
            return compare_angles(
                t1 - .25, (t2 - .25) % 1)


class Wall(Vector):
    def __init__(self, origin, end):
        ox, oy = origin
        fx, fy = end
        i = fx - ox
        j = fy - oy
        super(Wall, self).__init__(i, j)

        self.origin = origin

    def __repr__(self):
        origin = tuple(self.origin)
        angle = self.get_angle()
        end = self.apply_to_point(self.origin)

        return "Wall: angle: {}, {} to {}".format(
            angle, origin, end)

    @property
    def end_point(self):
        return self.apply_to_point(self.origin)

    @staticmethod
    def get_from_vector(vector, origin=(0, 0)):
        i, j = vector.get_value()
        ox, oy = origin
        i += ox
        j += oy

        origin = ox, oy
        end = i, j

        return Wall(origin, end)

    def get_rect(self):
        w, h = self.get_value()
        w = abs(w)
        h = abs(h)

        if w < 1:
            w = 1
        if h < 1:
            h = 1

        ox, oy = self.origin
        fx, fy = self.apply_to_point(self.origin)
        px, py = ox, oy

        if ox > fx:
            px = fx

        if oy > fy:
            py = fy

        return Rect((w, h), (px, py))

    def get_normal(self):
        normal = Vector(1, 0)
        normal.set_angle(self.get_angle())
        normal.rotate(.25)

        return normal

    def get_copy(self, rotate=0.0, scale=1):
        v = super(Wall, self).get_copy(rotate=rotate, scale=scale)

        return Wall.get_from_vector(v, self.origin)

    def rotate_around(self, point, angle):
        px, py = point
        ox, oy = self.origin
        dx = ox - px
        dy = oy - py

        d = Vector(dx, dy)
        d.rotate(angle)
        self.rotate(angle)

        self.origin = d.apply_to_point(point)

    # Returns the collision point for the underlying axes of two vector objects.
    # Returns False if the axes are parallel.
    def axis_collision(self, wall, origin=False):
        if origin:
            w = Wall.get_from_vector(wall, origin)
        else:
            w = wall.get_copy()

        delta = .75 - self.get_angle()                  # defines offset angle from y-axis

        w.rotate_around(self.origin, delta)             # rotate other vector about the origin
        wx, wy = w.origin
        wx -= self.origin[0]

        y_int = w.get_y_intercept((wx, wy))             # get the y-intercept of the other vector

        if y_int is False:
            return False

        y_int -= self.origin[1]

        collision = Vector(0, y_int)
        collision.rotate(-delta)                        # rotate back around to the original angle

        return collision.apply_to_point(self.origin)    # output the offset of other vector to first vector's origin

    # Returns the collision point of two vectors. Returns False if the two vectors are parallel
    def vector_collision(self, vector, origin):
        axis_collision = self.axis_collision(vector, origin)      # get axis collision...

        if not axis_collision:
            return False

        def point_in_bounds(w):
            x, y = axis_collision
            sx, sy = w.origin
            fx, fy = w.apply_to_point(
                w.origin)

            if fx > sx:
                x_bound = sx - 1 <= x <= fx + 1
            else:
                x_bound = sx + 1 >= x >= fx - 1
            if fy > sy:
                y_bound = sy - 1 <= y <= fy + 1
            else:
                y_bound = sy + 1 >= y >= fy - 1

            return x_bound and y_bound

        wall = Wall.get_from_vector(vector, origin)
        if point_in_bounds(self) and point_in_bounds(wall):
            return axis_collision                                  # check if it's within the bounds of both vectors

        else:
            return False

    def get_normal_adjustment(self, point, scale=1):
        x, y = point
        normal = self.get_normal()
        nx, ny = self.axis_collision(
            normal, (x, y))

        dx = x - nx
        dx *= scale
        dy = y - ny
        dy *= scale
        adjustment = Vector(-dx, -dy)

        return adjustment.get_value()


class Matrix:
    # [[a, c],
    #  [b, d]]
    # i_hat = ax + by       ae + bg     af + bh
    # j_hat = cx + dy       ce + dg     cf + dh
    def __init__(self, values):
        self.values = values

        self.a, self.b = values[0]
        self.c, self.d = values[1]

    @staticmethod
    def get_from_vectors(i, j):
        m = [
            [i.i_hat, j.i_hat],
            [i.j_hat, j.j_hat]
        ]
        return Matrix(m)

    def get_vectors(self):
        return (
            Vector(self.a, self.c),
            Vector(self.b, self.d)
        )

    def multiply_vector(self, vector):
        x, y = vector.get_value()
        ax = self.a * x
        by = self.b * y
        cx = self.c * x
        dy = self.d * y
        i = ax + by
        j = cx + dy

        return i, j

    def multiply_matrix(self, matrix):
        i, j = matrix.get_vectors()

        new_i = self.multiply_vector(i)
        new_j = self.multiply_vector(j)

        values = [
            [new_i[0], new_j[0]],
            [new_i[1], new_j[1]]
        ]

        return values
