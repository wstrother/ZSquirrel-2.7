from entities import Layer
from geometry import Rect
from resources import Image
from app.pygame_screen import render_graphics
from graphics import ImageGraphics


class CameraGraphics(ImageGraphics):
    def __init__(self, entity):
        super(CameraGraphics, self).__init__(entity, None)

    def update(self):
        entity = self.entity
        self.set_image(
            entity.screen, entity.world_position,
            *entity.camera_layers,
            scale=entity.scale
        )

    def set_image(self, screen, world_position, *layers, scale=1.0):
        self.image = self.get_screen_image(
            screen, world_position,
            *layers, scale=scale
        )

    @staticmethod
    def get_screen_image(screen, world_position, *layers, scale=1.0):
        if scale != 1.0:
            screen = screen.get_scaled(1 / scale)
        screen.fill((0, 0, 0, 0))

        args = []

        wx, wy = world_position
        wx *= -1
        wy *= -1

        for l in layers:
            args += l.get_graphics(offset=(wx, wy))

        for arg in args:
            render_graphics(screen, *arg)

        if scale != 1.0:
            screen = screen.get_scaled(scale)

        return screen


class CameraLayer(Layer):
    def __init__(self, name):
        super(CameraLayer, self).__init__(name)
        self.screen = None

        self.world_position = 0, 0
        self.scale = 1
        self._screen_rect = Rect(self.size, self.position)
        self.camera_layers = []

        self.make_screen()

        self.graphics = CameraGraphics(self)
        self.update_methods.append(self.graphics.update)

    # properties
    @property
    def screen_rect(self):
        r = self._screen_rect
        r.size = self.world_size
        r.position = self.world_position

        return r

    @property
    def world_size(self):
        w, h = self.size
        s = self.scale
        w /= s
        h /= s

        return w, h

    @property
    def focal_point(self):
        return self.screen_rect.center

    # setters
    def make_screen(self):
        w, h = self.size
        s = self.scale
        w /= s
        h /= s

        self.screen = Image.get_surface((w, h))

    def set_camera_layers(self, *layers):
        self.add_to_list("camera_layers", *layers)

    def get_camera_layers(self):
        return self.camera_layers

    def set_world_position(self, x, y):
        self.world_position = x, y

    def set_size(self, w, h):
        super(CameraLayer, self).set_size(w, h)

        if self.initialized:
            self.make_screen()

    def set_scale(self, scale):
        self.scale = scale
        self.make_screen()

    # # graphics rendering
    # def get_graphics(self, offset=None):
    #     if not offset:
    #         offset = self.position
    #     self.screen.fill((0, 0, 0, 0))
    #
    #     wx, wy = self.world_position
    #     wx *= -1
    #     wy *= -1
    #
    #     args = super(CameraLayer, self).get_graphics(
    #         offset=(wx, wy)
    #     )
    #
    #     for arg in args:
    #         self.render_graphics(*arg)
    #
    #     screen = self.screen
    #     if self.scale != 1:
    #         screen = self.screen.get_scaled(self.scale)
    #
    #     return [(screen, offset)]
    #
    # def render_graphics(self, image, *args):
    #     render_graphics(
    #         self.screen, image, *args
    #     )

    # camera methods
    def move_camera(self, dx, dy, v=1):
        r = self.screen_rect
        dx *= v
        dy *= v
        r.move((dx, dy))

        self.set_world_position(*r.position)

    def track_point(self, point, v=1):
        cx, cy = self.focal_point
        px, py = point

        dx = px - cx
        dy = py - cy

        if abs(dx) < .1:
            dx = 0

        if abs(dy) < .1:
            dy = 0

        self.move_camera(dx, dy, v=v)

    def zoom_to_scale(self, scale):
        cx, cy = self.focal_point
        self.set_scale(scale)
        self.track_point((cx, cy))

    def get_screen_position(self, x, y):
        wx, wy = self.world_position
        s = self.scale

        dx = x - wx
        dy = y - wy
        dx *= s
        dy *= s

        return dx, dy

    def get_world_position(self, sx, sy):
        wx, wy = self.world_position
        s = self.scale

        x = wx + (sx * s)
        y = wy + (sy * s)

        return x, y
