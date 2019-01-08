from pygame import transform, Surface, SRCALPHA

from zs_constants import Settings
from zs2.geometry import Rect, Vector
from zs2.meters import Meter
from zs2.resources import load_resource, Image


class Graphics:
    def __init__(self, entity):
        self.entity = entity

    def get_graphics(self, position):
        pass


class ImageGraphics(Graphics):
    def __init__(self, entity, image):
        self.image = image
        self.mirror = False, False

        super(ImageGraphics, self).__init__(entity)

    def get_graphics(self, position):
        px, py = position
        image = self.image

        mirror_x, mirror_y = self.mirror
        if mirror_x or mirror_y:
            image = image.flip(mirror_x, mirror_y)

        ex, ey = self.entity.position
        ex += px
        ey += py
        args = (image, (ex, ey))

        return [args]

    def reset_image(self):
        pass


class TextGraphics(ImageGraphics):
    def __init__(self, entity):
        image = self.make_text_image(
            entity.text, entity.style
        )
        super(TextGraphics, self).__init__(entity, image)

    @staticmethod
    def get_text(text, cutoff, nl):
        if type(text) == str:
            text = [text]

        for i in range(len(text)):
            line = str(text[i])
            line = line.replace("\t", "    ")
            line = line.replace("\r", "\n")
            if not nl:
                line = line.replace("\n", "")
            text[i] = line

        new_text = []

        for line in text:
            if cutoff:
                new_text += TextGraphics.format_text(
                    line, cutoff)
            else:
                if nl:
                    new_text += line.split("\n")
                else:
                    new_text += [line]

        if not new_text:
            new_text = [" "]

        return new_text

    @staticmethod
    def format_text(text, cutoff):
        f_text = []
        last_cut = 0

        for i in range(len(text)):
            char = text[i]
            done = False

            if char == "\n" and i - last_cut > 0:
                f_text.append(text[last_cut:i])
                last_cut = i + 1
                done = True

            if i == len(text) - 1:
                f_text.append(text[last_cut:])
                done = True

            if i - last_cut >= cutoff and not done:
                if char == " ":
                    f_text.append(text[last_cut:i])
                    last_cut = i + 1
                else:
                    search = True
                    x = i
                    while search:
                        x -= 1
                        if text[x] == " ":
                            next_line = text[last_cut:x]
                            last_cut = x + 1
                            f_text.append(next_line)
                            search = False
                        else:
                            if x <= last_cut:
                                next_line = text[last_cut:i]
                                last_cut = i
                                f_text.append(next_line)
                                search = False

        return f_text

    @staticmethod
    def make_text_image(text, style):
        font = style.get_font()
        color = style.font_color
        buffer = style.text_buffer
        cutoff = style.text_cutoff
        nl = style.text_newline

        text = TextGraphics.get_text(
            text, cutoff, nl)

        line_images = []
        for line in text:
            line_images.append(
                font.render(line, 1, color))

        widest = sorted(line_images, key=lambda l: -1 * l.get_size()[0])[0]
        line_height = (line_images[0].get_size()[1] + buffer)
        w, h = widest.get_size()[0], (line_height * len(line_images)) - buffer

        sprite_image = Surface(
            (w, h), SRCALPHA, 32
        )

        for i in range(len(line_images)):
            image = line_images[i]
            y = line_height * i
            sprite_image.blit(image, (0, y))

        return Image(sprite_image)

    def reset_image(self):
        self.image = self.make_text_image(
            self.entity.text, self.entity.style
        )


class LayeredImageGraphics(ImageGraphics):
    def __init__(self, entity, image):
        super(LayeredImageGraphics, self).__init__(entity, image)

        self.layers = []

    def get_graphics(self, position):
        if not self.layers:
            return super(LayeredImageGraphics, self).get_graphics(position)

        else:
            px, py = position
            args = []

            for l in self.layers:
                a = self.get_args_from_layer(l)
                lx, ly = a[1]
                lx += px
                ly += py
                a = (a[0], (lx, ly))
                args.append(a)

            return args

    # layer = (rect, draw_offset, mirror=(False, False), rotate=0)
    # rect = Rect(size, position) object
    # draw_offset = (ox, oy)  (int, int)
    # mirror = x_bool, y_bool
    # rotate = float
    def get_args_from_layer(self, layer):
        rect, offset = layer[0:2]
        image = self.image.subsurface(rect)

        mirror = False, False
        rotate = 0
        if len(layer) > 2:
            mirror = layer[2]

            if len(layer) > 3:
                rotate = layer[3]

        mirror_x, mirror_y = mirror
        if mirror_x or mirror_y:
            image = image.flip(mirror_x, mirror_y)

        # if rotate:
        #   image = image.get_rotated(rotate)

        px, py = self.entity.position
        ox, oy = offset
        px += ox
        py += oy

        layer_args = (image, (px, py))

        return layer_args


class TileMapGraphics(LayeredImageGraphics):
    def __init__(self, entity, image):
        super(TileMapGraphics, self).__init__(entity, image)

        self.tile_size = 1, 1                   # pixel size of single tile

    # layer = (position, tile_offset)
    # position = (col, row)  (int, int)         cell position on tile grid
    # tile_offset = (ox, oy) (int, int)         pixel offset on tile image
    def get_args_from_layer(self, layer):
        position, tile_offset = layer
        col, row = position
        tw, th = self.tile_size
        x = col * tw
        y = row * th

        rect = Rect(self.tile_size, tile_offset)
        layer = rect, (x, y)

        return super(TileMapGraphics, self).get_args_from_layer(layer)

    def flatten(self):
        surface = Surface(self.entity.size, SRCALPHA)

        for t in self.layers:
            image, offset = self.get_args_from_layer(t)

            surface.blit(image.pygame_surface, offset)

        self.layers = []
        self.image = Image(surface)


class AnimationGraphics(LayeredImageGraphics):
    def __init__(self, entity, image):
        super(AnimationGraphics, self).__init__(entity, image)

        self.animations = {}
        self.animation_meter = Meter(
            "{} animation meter".format(entity.name),
            0, 0, 1
        )

        self.animation_cycles = 0

    def update(self):
        meter = self.animation_meter
        if meter.is_full():
            self.animation_cycles += 1

        meter.next()
        self.update_image_layers()

    def update_image_layers(self):
        state = self.entity.get_animation_state()
        self.layers = []

        if state in self.animations:
            animation = self.animations[state]
            step = animation.get_current_step(self.animation_meter.value)

            for layer in step.layers:
                rect = Rect(layer.size, layer.position)
                offset = layer.offset
                mirror = layer.mirror
                rotate = layer.rotate

                self.layers.append((rect, offset, mirror, rotate))

    def reset_meter(self):
        state = self.entity.get_animation_state()
        self.animation_cycles = 0
        self.animation_meter.reset()

        if state in self.animations:
            animation = self.animations[state]
            self.animation_meter.maximum = animation.get_frame_count() - 1
            self.update_image_layers()


class ContainerGraphics(ImageGraphics):
    PRE_RENDERS = {}

    def __init__(self, entity):
        image = self.get_rect_image(entity.size, entity.style)
        super(ContainerGraphics, self).__init__(entity, image)

    @staticmethod
    def get_rect_image(size, style):
        bg_color = style.bg_color
        if not bg_color:
            bg_color = 0, 0, 0

        image = ContainerGraphics.make_color_image(
            size, bg_color)

        # BG TILE IMAGE
        if style.bg_image:
            image = ContainerGraphics.tile(
                style.bg_image, image)

        # BORDERS
        if style.border:
            border_images = style.border_images
            sides = style.border_sides
            corners = style.border_corners

            image = ContainerGraphics.make_border_image(
                border_images, image, sides, corners
            )

        # BORDER ALPHA TRIM
        if style.alpha_color:
            image = ContainerGraphics.convert_colorkey(
                image, style.alpha_color
            )

        return Image(image)

    def reset_image(self):
        self.image = self.get_rect_image(
            self.entity.size, self.entity.style
        )

    @staticmethod
    def tile(image_name, surface):
        # PYGAME CHOKE POINT

        if image_name not in ContainerGraphics.PRE_RENDERS:
            bg_image = load_resource(image_name)
            sx, sy = Settings.SCREEN_SIZE  # pre render the tiled background
            sx *= 2  # to the size of a full screen
            sy *= 2
            pr_surface = Surface(
                (sx, sy), SRCALPHA, 32)

            w, h = pr_surface.get_size()
            img_w, img_h = bg_image.get_size()

            for x in range(0, w + img_w, img_w):
                for y in range(0, h + img_h, img_h):
                    pr_surface.blit(bg_image.pygame_surface, (x, y))

            ContainerGraphics.PRE_RENDERS[image_name] = pr_surface

        full_bg = ContainerGraphics.PRE_RENDERS[image_name]     # return a subsection of the full
        #                                                       # pre rendered background
        r = surface.get_rect().clip(full_bg.get_rect())
        blit_region = full_bg.subsurface(r)
        surface.blit(blit_region, (0, 0))

        return surface

    @staticmethod
    def make_color_image(size, color):
        # PYGAME CHOKE POINT

        s = Surface(size).convert()
        if color:
            s.fill(color)
        else:
            s.set_colorkey(s.get_at((0, 0)))

        return s

    @staticmethod
    def convert_colorkey(surface, colorkey):
        surface.set_colorkey(colorkey)

        return surface

    @staticmethod
    def make_border_image(border_images, surface, sides, corners):
        h_side_image, v_side_image, corner_image = border_images

        draw_corners = ContainerGraphics.draw_corners
        full_h_side = ContainerGraphics.get_h_side(h_side_image)
        full_v_side = ContainerGraphics.get_v_side(v_side_image)

        w, h = surface.get_size()

        if "l" in sides:
            surface.blit(full_h_side, (0, 0))

        if "r" in sides:
            h_offset = w - full_h_side.get_size()[0]
            surface.blit(transform.flip(
                full_h_side, True, False), (h_offset, 0))

        if "t" in sides:
            surface.blit(full_v_side, (0, 0))

        if "b" in sides:
            v_offset = h - full_v_side.get_size()[1]
            surface.blit(transform.flip(
                full_v_side, False, True), (0, v_offset))

        if corners:
            draw_corners(corner_image, surface, corners)

        return surface

    @staticmethod
    def get_h_side(image):
        return ContainerGraphics.get_full_side_image(image, "h")

    @staticmethod
    def get_v_side(image):
        return ContainerGraphics.get_full_side_image(image, "v")

    @staticmethod
    def get_full_side_image(image_name, orientation):
        if image_name not in ContainerGraphics.PRE_RENDERS:
            image = load_resource(image_name)
            iw, ih = image.get_size()

            h, v = "hv"
            size = {h: (iw, Settings.SCREEN_SIZE[1]),
                    v: (Settings.SCREEN_SIZE[0], iw)}[orientation]
            pr_surface = Surface(
                size, SRCALPHA, 32)

            span = {h: range(0, size[1], ih),
                    v: range(0, size[0], iw)}[orientation]

            for i in span:
                position = {h: (0, i),
                            v: (i, 0)}[orientation]
                pr_surface.blit(image.pygame_surface, position)

            ContainerGraphics.PRE_RENDERS[image_name] = pr_surface

        return ContainerGraphics.PRE_RENDERS[image_name]

    @staticmethod
    def draw_corners(image_name, surface, corners):
        corner_image = load_resource(image_name)
        w, h = surface.get_size()
        cw, ch = corner_image.get_size()
        a, b, c, d = "abcd"
        locations = {a: (0, 0),
                     b: (w - cw, 0),
                     c: (0, h - ch),
                     d: (w - cw, h - ch)}

        for corner in corners:
            surface.blit(
                ContainerGraphics.get_corner(corner_image, corner).pygame_surface,
                locations[corner]
            )

    @staticmethod
    def get_corner(img, string):
        a, b, c, d = "abcd"
        corner = {a: lambda i: i,
                  b: lambda i: i.flip(True, False),
                  c: lambda i: i.flip(False, True),
                  d: lambda i: i.flip(True, True)
                  }[string](img)

        return corner


class GeometryGraphics(Graphics):
    def __init__(self, entity):
        super(GeometryGraphics, self).__init__(entity)

        self.items = []

    def get_rect_args(self, r, position):
        r.move(position)
        color = self.entity.draw_color
        if r.color:
            color = r.color

        return (
            "rect", color, r, self.entity.draw_width
        )

    def get_vector_args(self, v, position):
        color = self.entity.draw_color

        if type(v) in (list, tuple):
            start = v[1]
            v = v[0]
        else:
            start = getattr(v, "origin", self.entity.position)

        if self.entity.vector_scale != 1:
            v = v.get_copy(scale=self.entity.vector_scale)

        if v.color:
            color = v.color

        end = v.apply_to_point(start)
        width = self.entity.draw_width

        sx, sy = start
        ex, ey = end
        px, py = position
        sx += px
        ex += px
        sy += py
        ey += py

        return (
            "line", color, (sx, sy), (ex, ey), width
        )

    def get_graphics(self, position):
        args = []

        for i in self.items:
            if type(i) is Rect:
                args.append(self.get_rect_args(i, position))

            elif isinstance(i, Vector) or isinstance(i[0], Vector):
                args.append(self.get_vector_args(i, position))

        return args
