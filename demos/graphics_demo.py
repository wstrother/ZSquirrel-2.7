from game import Game, PygameScreen
from entities import Layer, Sprite
from context import Context, ApplicationInterface
from graphics import ImageGraphics, ImageSectionGraphics, GeometryGraphics
from geometry import Rect, Vector, Wall


class GraphicsInterface(ApplicationInterface):
    def __init__(self, *args):
        super(GraphicsInterface, self).__init__(*args)

        self.init_order = [
            self.set_image.__name__,
            self.set_image_sections.__name__
        ]

    def set_image(self, sprite, file_name, sub=None):
        if not sub:
            image = self.context.load_resource(file_name)
        else:
            x, y, w, h = sub
            size, position = (w, h), (x, y)

            image = self.context.load_resource(
                file_name
            ).subsurface(Rect(size, position))

        graphics = ImageGraphics(sprite, image)
        sprite.graphics = graphics

    @staticmethod
    def set_color_key(sprite, x, y):
        image = sprite.graphics.image
        image.set_color_key((x, y))

    def set_image_sections(self, sprite, file_name, *sections):
        image = self.context.load_resource(file_name)
        graphics = ImageSectionGraphics(sprite, image)

        for section in sections:
            x, y, w, h = section[:4]
            rect = Rect((w, h), (x, y))

            ox, oy = 0, 0
            if len(section) > 4:
                ox, oy = section[4:6]

            mx, my = False, False
            if len(section) > 6:
                mx, my = section[6:]

            graphics.layers.append(
                (rect, (ox, oy), (mx, my))
            )

        sprite.graphics = graphics

    def set_rect_image(self, sprite, *args):
        if sprite.graphics is None:
            sprite.graphics = GeometryGraphics(sprite)

        if len(args) > 1:
            color, width = args
        else:
            color = args[0]
            width = 1

        rect = Rect(sprite.size, (0, 0))
        sprite.graphics.items.append(
            (rect, color, width)
        )

        sprite.update_methods.append(
            lambda: self.update_rect_image(sprite, rect)
        )

    @staticmethod
    def update_rect_image(sprite, rect):
        rect.size = sprite.size

    @staticmethod
    def set_line_image(sprite, *args):
        if sprite.graphics is None:
            sprite.graphics = GeometryGraphics(sprite)

        if len(args) > 3:
            color, start, end, width = args
        else:
            color, start, end = args
            width = 1

        ox, oy = start
        if (ox, oy) == (0, 0):
            v = Vector(*end)
        else:
            v = Wall(start, end)

        sprite.graphics.items.append(
            (v, color, width)
        )

    @staticmethod
    def set_draw_method(sprite, *args):
        if sprite.graphics is None:
            sprite.graphics = GeometryGraphics(sprite)
        sprite.graphics.items.append(args)


def main():
    scr = PygameScreen((1100, 600))
    c = Context.get_default_context(
        Game(scr),
        [
            Sprite,
            Layer
        ],
        [
            GraphicsInterface
        ]
    )

    c.load_environment("graphics_demo.json")
    c.run_game()
