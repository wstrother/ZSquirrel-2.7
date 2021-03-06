from zsquirrel.context import ApplicationInterface
from zsquirrel.utils.geometry import Rect, Vector, Wall, add_points
import zsquirrel.constants as con


class Graphics:
    def __init__(self, entity):
        self.entity = entity

    def get_graphics(self, offset):
        pass


class ImageGraphics(Graphics):
    def __init__(self, entity, image):
        self.image = image
        self.mirror = False, False

        super(ImageGraphics, self).__init__(entity)

    def get_graphics(self, offset):
        image = self.image

        mirror_x, mirror_y = self.mirror
        if mirror_x or mirror_y:
            image = image.flip(mirror_x, mirror_y)

        position = add_points(
            self.entity.position, offset
        )
        args = (image, position)

        return [args]


class ImageSectionGraphics(ImageGraphics):
    def __init__(self, entity, image):
        super(ImageSectionGraphics, self).__init__(entity, image)

        self.layers = []

    def get_graphics(self, offset):
        if not self.layers:
            return super(ImageSectionGraphics, self).get_graphics(offset)

        else:
            args = []

            for layer in self.layers:
                a = self.get_section_args(layer)
                position = add_points(a[1], offset)
                a = (a[0], position)
                args.append(a)

            return args

    # section = (rect, draw_offset, mirror=(False, False))
    # rect = Rect(size, position)   object
    # draw_offset = (ox, oy)        (int, int)
    # mirror = (x_bool, y_bool)     (bool, bool)
    def get_section_args(self, section):
        rect, offset = section[0:2]
        image = self.image.subsurface(rect)

        mirror = False, False

        if len(section) > 2:
            mirror = section[2]

        mirror_x, mirror_y = mirror
        if mirror_x or mirror_y:
            image = image.flip(mirror_x, mirror_y)

        px, py = self.entity.position
        ox, oy = offset
        px += ox
        py += oy

        layer_args = (image, (px, py))

        return layer_args


class GeometryGraphics(Graphics):
    def __init__(self, entity):
        super(GeometryGraphics, self).__init__(entity)

        self.items = []

    # item = (Rect, draw_color, draw_width=1)
    @staticmethod
    def get_rect_args(item, offset):
        if len(item) < 3:
            rect, color = item
            width = 0
        else:
            rect, color, width = item

        x, y = add_points(offset, rect.position)
        rect = rect.pygame_rect
        rect.x = int(x)
        rect.y = int(y)

        return (
            con.PYGAME_RECT, color, rect, width
        )

    # v = (Vector, draw_color, draw_width=1)
    @staticmethod
    def get_vector_args(item, offset):
        if len(item) < 3:
            vector, color = item
            width = 1
        else:
            vector, color, width = item

        end = vector.apply_to_point(offset)
        end = int(end[0]), int(end[1])

        return (
            con.PYGAME_LINE, color, offset, end, width
        )

    def get_graphics(self, offset=None):
        if not offset:
            offset = 0, 0
        offset = add_points(self.entity.position, offset)
        offset = int(offset[0]), int(offset[1])

        args = []

        for item in self.items:
            if type(item[0]) is Rect:
                args.append(self.get_rect_args(item, offset))

            elif type(item[0]) is Vector:
                args.append(self.get_vector_args(item, offset))

            elif type(item[0]) is Wall:
                args.append(self.get_vector_args(
                    item, add_points(offset, item[0].origin)
                ))

            elif item[0] == con.PYGAME_LINE:
                item[2] = add_points(offset, item[2])
                item[3] = add_points(offset, item[3])
                args.append(item)

            elif item[0] == con.PYGAME_RECT:
                item[2].x += offset[0]
                item[2].y += offset[1]
                args.append(item)

            elif item[0] == con.PYGAME_CIRCLE:
                item = list(item)
                item[2] = add_points(offset, item[2])
                args.append(item)

        return args


class GraphicsInterface(ApplicationInterface):
    def __init__(self, *args):
        super(GraphicsInterface, self).__init__(*args)

        self.init_order = [
            self.set_image.__name__,
            self.set_image_sections.__name__
        ]

    def set_image(self, entity, file_name, sub=None):
        if not sub:
            image = self.context.load_resource(file_name)
        else:
            x, y, w, h = sub
            size, position = (w, h), (x, y)

            image = self.context.load_resource(
                file_name
            ).subsurface(Rect(size, position))

        graphics = ImageGraphics(entity, image)
        entity.graphics = graphics

    @staticmethod
    def set_color_key(entity, x, y):
        image = entity.graphics.image
        image.set_color_key((x, y))

    def set_image_sections(self, entity, file_name, *sections):
        image = self.context.load_resource(file_name)
        graphics = ImageSectionGraphics(entity, image)

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

        entity.graphics = graphics

    def set_rect_image(self, entity, *args):
        if entity.graphics is None:
            entity.graphics = GeometryGraphics(entity)

        if len(args) > 1:
            color, width = args
        else:
            color = args[0]
            width = 1

        rect = Rect(entity.size, (0, 0))
        entity.graphics.items.append(
            (rect, color, width)
        )

        entity.update_methods.append(
            lambda: self.update_rect_image(entity, rect)
        )

    @staticmethod
    def update_rect_image(entity, rect):
        rect.size = entity.size

    @staticmethod
    def set_vector_image(entity, *args):
        if entity.graphics is None:
            entity.graphics = GeometryGraphics(entity)

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

        entity.graphics.items.append(
            (v, color, width)
        )

    @staticmethod
    def set_draw_method(entity, *args):
        if entity.graphics is None:
            entity.graphics = GeometryGraphics(entity)
        entity.graphics.items.append(args)
