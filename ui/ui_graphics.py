from pygame import SRCALPHA, transform
from pygame.surface import Surface
from graphics import ImageGraphics
from resources import Image


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

#
# class ContainerGraphics(ImageGraphics):
#     PRE_RENDERS = {}
#
#     def __init__(self, entity):
#         image = self.get_rect_image(entity.size, entity.style)
#         super(ContainerGraphics, self).__init__(entity, image)
#
#     @staticmethod
#     def get_rect_image(size, style):
#         bg_color = style.bg_color
#         if not bg_color:
#             bg_color = 0, 0, 0
#
#         image = ContainerGraphics.make_color_image(
#             size, bg_color)
#
#         # BG TILE IMAGE
#         if style.bg_image:
#             image = ContainerGraphics.tile(
#                 style.bg_image, image)
#
#         # BORDERS
#         if style.border:
#             border_images = style.border_images
#             sides = style.border_sides
#             corners = style.border_corners
#
#             image = ContainerGraphics.make_border_image(
#                 border_images, image, sides, corners
#             )
#
#         # BORDER ALPHA TRIM
#         if style.alpha_color:
#             image = ContainerGraphics.convert_colorkey(
#                 image, style.alpha_color
#             )
#
#         return Image(image)
#
#     def reset_image(self):
#         self.image = self.get_rect_image(
#             self.entity.size, self.entity.style
#         )
#
#     @staticmethod
#     def tile(image_name, surface):
#         # PYGAME CHOKE POINT
#
#         if image_name not in ContainerGraphics.PRE_RENDERS:
#             bg_image = load_resource(image_name)
#             sx, sy = Settings.SCREEN_SIZE  # pre render the tiled background
#             sx *= 2  # to the size of a full screen
#             sy *= 2
#             pr_surface = Surface(
#                 (sx, sy), SRCALPHA, 32)
#
#             w, h = pr_surface.get_size()
#             img_w, img_h = bg_image.get_size()
#
#             for x in range(0, w + img_w, img_w):
#                 for y in range(0, h + img_h, img_h):
#                     pr_surface.blit(bg_image.pygame_surface, (x, y))
#
#             ContainerGraphics.PRE_RENDERS[image_name] = pr_surface
#
#         full_bg = ContainerGraphics.PRE_RENDERS[image_name]     # return a subsection of the full
#         #                                                       # pre rendered background
#         r = surface.get_rect().clip(full_bg.get_rect())
#         blit_region = full_bg.subsurface(r)
#         surface.blit(blit_region, (0, 0))
#
#         return surface
#
#     @staticmethod
#     def make_color_image(size, color):
#         # PYGAME CHOKE POINT
#
#         s = Surface(size).convert()
#         if color:
#             s.fill(color)
#         else:
#             s.set_colorkey(s.get_at((0, 0)))
#
#         return s
#
#     @staticmethod
#     def convert_colorkey(surface, colorkey):
#         surface.set_colorkey(colorkey)
#
#         return surface
#
#     @staticmethod
#     def make_border_image(border_images, surface, sides, corners):
#         h_side_image, v_side_image, corner_image = border_images
#
#         draw_corners = ContainerGraphics.draw_corners
#         full_h_side = ContainerGraphics.get_h_side(h_side_image)
#         full_v_side = ContainerGraphics.get_v_side(v_side_image)
#
#         w, h = surface.get_size()
#
#         if "l" in sides:
#             surface.blit(full_h_side, (0, 0))
#
#         if "r" in sides:
#             h_offset = w - full_h_side.get_size()[0]
#             surface.blit(transform.flip(
#                 full_h_side, True, False), (h_offset, 0))
#
#         if "t" in sides:
#             surface.blit(full_v_side, (0, 0))
#
#         if "b" in sides:
#             v_offset = h - full_v_side.get_size()[1]
#             surface.blit(transform.flip(
#                 full_v_side, False, True), (0, v_offset))
#
#         if corners:
#             draw_corners(corner_image, surface, corners)
#
#         return surface
#
#     @staticmethod
#     def get_h_side(image):
#         return ContainerGraphics.get_full_side_image(image, "h")
#
#     @staticmethod
#     def get_v_side(image):
#         return ContainerGraphics.get_full_side_image(image, "v")
#
#     @staticmethod
#     def get_full_side_image(image_name, orientation):
#         if image_name not in ContainerGraphics.PRE_RENDERS:
#             image = load_resource(image_name)
#             iw, ih = image.get_size()
#
#             h, v = "hv"
#             size = {h: (iw, Settings.SCREEN_SIZE[1]),
#                     v: (Settings.SCREEN_SIZE[0], iw)}[orientation]
#             pr_surface = Surface(
#                 size, SRCALPHA, 32)
#
#             span = {h: range(0, size[1], ih),
#                     v: range(0, size[0], iw)}[orientation]
#
#             for i in span:
#                 position = {h: (0, i),
#                             v: (i, 0)}[orientation]
#                 pr_surface.blit(image.pygame_surface, position)
#
#             ContainerGraphics.PRE_RENDERS[image_name] = pr_surface
#
#         return ContainerGraphics.PRE_RENDERS[image_name]
#
#     @staticmethod
#     def draw_corners(image_name, surface, corners):
#         corner_image = load_resource(image_name)
#         w, h = surface.get_size()
#         cw, ch = corner_image.get_size()
#         a, b, c, d = "abcd"
#         locations = {a: (0, 0),
#                      b: (w - cw, 0),
#                      c: (0, h - ch),
#                      d: (w - cw, h - ch)}
#
#         for corner in corners:
#             surface.blit(
#                 ContainerGraphics.get_corner(corner_image, corner).pygame_surface,
#                 locations[corner]
#             )
#
#     @staticmethod
#     def get_corner(img, string):
#         a, b, c, d = "abcd"
#         corner = {a: lambda i: i,
#                   b: lambda i: i.flip(True, False),
#                   c: lambda i: i.flip(False, True),
#                   d: lambda i: i.flip(True, True)
#                   }[string](img)
#
#         return corner
