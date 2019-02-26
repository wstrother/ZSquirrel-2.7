from pygame.font import match_font, Font
import pygame
import constants as con

pygame.init()


class Style:
    LOADED_FONTS = {}
    DEFAULT_DATA = {
            con.BORDER_CORNERS: "",                     # 'a|b|c|d'
            con.BORDER_SIZE: con.DEFAULT_BORDER_SIZE,   # [int, int]
            con.BORDER_SIDES: "",                       # 't|l|r|b'
            con.BORDER_IMAGES: None,                    # None or [h_side: str, v_side: str, corner: str]
            con.BORDER: False,                          # bool

            con.ALIGNS: con.DEFAULT_ALIGNS,             # ['l' or 'c' or 'r', 't' or 'c' or 'b']
            con.BUFFERS: [0, 0],                        # [int, int]

            con.FONT_COLOR: con.DEFAULT_FONT_COLOR,     # [0-255, 0-255, 0-255]
            con.FONT_SIZE: con.DEFAULT_FONT_SIZE,       # int
            con.FONT_NAME: con.DEFAULT_FONT_NAME,       # str
            con.TEXT_BUFFER: 0,                         # int
            con.TEXT_CUTOFF: con.DEFAULT_TEXT_CUTOFF,   # int
            con.TEXT_NEWLINE: False,                    # bool
            con.BOLD: True,                             # bool
            con.ITALIC: False,                          # bool
            con.BG_IMAGE: None,                         # None or str

            con.BG_COLOR: con.DEFAULT_BG_COLOR,         # [0-255, 0-255, 0-255]
            con.ALPHA_COLOR: con.DEFAULT_ALPHA_COLOR,   # [0-255, 0-255, 0-255]
            con.SELECTED: con.DEFAULT_SELECT_COLOR,     # [0-255, 0-255, 0-255]
            con.NORMAL: con.DEFAULT_FONT_COLOR          # [0-255, 0-255, 0-255]
        }

    def __init__(self, data=None):
        self.set_style(Style.DEFAULT_DATA)

        if data:
            self.set_style(data)

    def set_style(self, data):
        self.__dict__.update(data)

    def get_color(self, name):
        if name in self.__dict__:
            return self.__dict__[name]

    def get_font(self):
        name = self.__dict__[con.FONT_NAME]
        size = self.__dict__[con.FONT_SIZE]
        bold = self.__dict__[con.BOLD]
        italic = self.__dict__[con.ITALIC]
        return self.load_font(name, size, bold, italic)

    def get_data(self):
        return self.__dict__.copy()

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
