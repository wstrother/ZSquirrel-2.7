from graphics import ImageGraphics
from resources import Image
import constants as con
from geometry import Rect


class TextGraphics(ImageGraphics):
    def __init__(self, entity, text, style):
        self.text = text
        image = self.make_text_image(
            text, style
        )
        super(TextGraphics, self).__init__(entity, image)
        self.entity.set_size(*image.get_size())

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

        sprite_image = Image.get_surface((w, h))

        for i in range(len(line_images)):
            image = line_images[i]
            y = line_height * i
            sprite_image.blit(image, (0, y))

        return Image(sprite_image)

    def set_text(self, text, style):
        self.text = text
        self.image = self.make_text_image(
            text, style
        )
        self.entity.set_size(*self.image.get_size())


class ContainerGraphics(ImageGraphics):
    def __init__(self, entity, tile_render=None, border_images=None):
        self.tile_render = tile_render
        self.border_images = border_images

        image = self.get_rect_image(
            entity.size, entity.style,
            tile_render=tile_render,
            border_images=border_images
        )
        super(ContainerGraphics, self).__init__(entity, image)

    def reset_image(self):
        self.image = self.get_rect_image(
            self.entity.size, self.entity.style,
            self.tile_render, self.border_images
        )

    @staticmethod
    def get_rect_image(size, style, tile_render=None, border_images=None):
        image = Image.get_surface(
            size, style.bg_color)

        # BG TILE IMAGE
        if tile_render:
            image.blit(
                tile_render, (0, 0), Rect(size)
            )

        # BORDERS
        if border_images and style.border:
            sides = style.border_sides
            corners = style.border_corners

            image = ContainerGraphics.add_borders(
                image, border_images, sides, corners
            )

        if style.alpha_color:
            s = Image.get_surface(image.get_size(), key=style.alpha_color)
            s.blit(image, (0, 0))
            image = s

        return Image(image)

    @staticmethod
    def tile_surface(tile_image, surface):
        w, h = surface.get_size()
        tw, th = tile_image.get_size()

        for x in range(0, w + tw, tw):
            for y in range(0, h + th, th):
                surface.blit(tile_image, (x, y))

        return surface

    @staticmethod
    def add_borders(surface, border_images, sides, corners):
        full_h_side, full_v_side, corner_image = border_images
        w, h = surface.get_size()
        t, l, r, b = con.SIDE_CHOICES

        if l in sides:
            surface.blit(full_h_side, (0, 0))

        if r in sides:
            h_offset = w - full_h_side.get_size()[0]
            surface.blit(
                full_h_side.flip(True, False), (h_offset, 0)
            )

        if t in sides:
            surface.blit(full_v_side, (0, 0))

        if b in sides:
            v_offset = h - full_v_side.get_size()[1]
            surface.blit(
                full_v_side.flip(False, True), (0, v_offset)
            )

        if corners:
            ContainerGraphics.add_corners(
                surface, corner_image, corners
            )

        return surface

    @staticmethod
    def add_corners(surface, corner_image, corners):
        w, h = surface.get_size()
        a, b, c, d = con.CORNER_CHOICES
        cw, ch = corner_image.get_size()
        locations = {
            a: (0, 0),
            b: (w - cw, 0),
            c: (0, h - ch),
            d: (w - cw, h - ch)
        }

        for corner in corners:
            surface.blit(
                ContainerGraphics.get_corner(corner_image, corner),
                locations[corner]
            )

    @staticmethod
    def get_corner(corner_image, corner):
        a, b, c, d = con.CORNER_CHOICES
        return {
            a: lambda i: i,
            b: lambda i: i.flip(True, False),
            c: lambda i: i.flip(False, True),
            d: lambda i: i.flip(True, True)
        }[corner](corner_image)
