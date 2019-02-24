from pygame.font import match_font, Font
import constants as con


class Style:
    LOADED_FONTS = {}

    def __init__(self, data):
        # borders
        self.border_corners = data[con.BORDER_CORNERS]   # 'abcd'
        self.border_size = data[con.BORDER_SIZE]         # [int, int]
        self.border_sides = data[con.BORDER_SIDES]       # 'tlrb'
        self.border = data[con.BORDER]                   # bool
        self.border_images = data[con.BORDER_IMAGES]     # [h_side, v_side, corner]

        # alignments, buffers
        self.aligns = data[con.ALIGNS]         # ['l|c|r|', 't|c|b']
        self.buffers = data[con.BUFFERS]       # [int, int]  ([h, v])

        # fonts, text
        self.font_color = data[con.FONT_COLOR]       # [int, int, int]
        self.font_size = data[con.FONT_SIZE]         # float
        self.font_name = data[con.FONT_NAME]         # str
        self.text_buffer = data[con.TEXT_BUFFER]     # int
        self.text_cutoff = data[con.TEXT_CUTOFF]     # int
        self.text_newline = data[con.TEXT_NEWLINE]   # bool
        self.bold = data[con.BOLD]                   # bool
        self.italic = data[con.ITALIC]               # bool

        # bg, color
        self.bg_image = data[con.BG_IMAGE]          # None or str
        self.bg_color = data[con.BG_COLOR]          # [int, int, int]
        self.alpha_color = data[con.ALPHA_COLOR]    # [int, int, int]

        self.selected = data[con.SELECTED]
        self.normal = data[con.NORMAL]

    def get_color(self, name):
        if name in self.__dict__:
            return self.__dict__[name]

    def get_font(self):
        return self.load_font(
            self.font_name, self.font_size,
            self.bold, self.italic
        )

    def get_copy(self):
        return self.__dict__

    @classmethod
    def load_font(cls, name, size, bold, italic):
        h_key = hash((name, size, bold, italic))

        if h_key in cls.LOADED_FONTS:
            return cls.LOADED_FONTS[h_key]

        else:
            path = match_font(name, bold, italic)
            font = Font(path, size)
            cls.LOADED_FONTS[h_key] = font

            return font
