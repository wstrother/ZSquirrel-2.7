from zs2.resources import get_font
from zs_constants import Settings


class Style:
    def __init__(self, data=None):
        # borders
        self.border_corners = ""        # 'abcd'
        self.border_size = [0, 0]       # [int, int]
        self.border_sides = ""          # 'tlrb'
        self.border = False             # bool
        self.border_images = [          # [h_side, v_side, corner]
            None, None, None
        ]

        # alignments, buffers
        self.aligns = ["c", "c"]        # ['l|c|r|', 't|c|b']
        self.buffers = [0, 0]           # [int, int]  ([h, v])

        # fonts, text
        self.font_color = Settings.FONT_COLOR                     # [int, int, int]
        self.font_size = Settings.DEFAULT_FONT_SIZE               # float
        self.font_name = ""             # str
        self.text_buffer = 1            # int
        self.text_cutoff = Settings.TEXT_CUTOFF                   # int
        self.text_newline = False       # bool
        self.bold = False               # bool
        self.italic = False             # bool

        # bg, color
        self.bg_image = None            # None or str
        self.bg_color = [0, 0, 0]       # [int, int, int]
        self.alpha_color = [0, 0, 0]    # [int, int, int]

        self.selected = Settings.FONT_HIGHLIGHT
        self.normal = Settings.FONT_COLOR

        if data:
            self.set_style(data)

    def get_color(self, name):
        if name in self.__dict__:
            return self.__dict__[name]

    def get_font(self):
        return get_font(
            self.font_name, self.font_size,
            self.bold, self.italic
        )

    def set_style(self, data):
        for name in data:
            if name in self.__dict__:
                self.__dict__[name] = data[name]

    def get_copy(self):
        return self.__dict__
