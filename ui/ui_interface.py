import constants as con
from context import ApplicationInterface
from entities import Sprite
from resources import Image
from ui.style import Style
from ui.flex import MemberTable
from ui.ui_graphics import TextGraphics, ContainerGraphics

PRE_RENDERS = {}


class UiGraphicsInterface(ApplicationInterface):
    def __init__(self, *args):
        super(UiGraphicsInterface, self).__init__(*args)

        self.init_order += [
            self.set_style.__name__
        ]

    def set_style(self, sprite, style):
        if type(style) is str:
            style = self.context.load_resource(style)

        if sprite.style is None:
            sprite.style = Style(style)

    @staticmethod
    def set_text(sprite, text):
        if sprite.style is None:
            sprite.style = Style()

        if sprite.graphics is None:
            sprite.graphics = TextGraphics(
                sprite, text, sprite.style
            )

        else:
            sprite.graphics.set_text(text, sprite.style)

    def set_container_image(self, sprite):
        if sprite.style is None:
            sprite.style = Style()

        tile_render = None
        tile = sprite.style.bg_image

        if tile:
            if tile not in PRE_RENDERS:
                PRE_RENDERS[tile] = self.get_tile_render(tile)

            tile_render = PRE_RENDERS[tile]

        border_images = None
        border = sprite.style.border

        if border and sprite.style.border_images:
            h_side, v_side, corner = sprite.style.border_images

            if h_side not in PRE_RENDERS:
                PRE_RENDERS[h_side] = self.get_border_render(
                    h_side, con.SIDE_CHOICES[1]
                )

            if v_side not in PRE_RENDERS:
                PRE_RENDERS[v_side] = self.get_border_render(
                    v_side, con.SIDE_CHOICES[0]
                )

            border_images = (
                PRE_RENDERS[h_side],
                PRE_RENDERS[v_side],
                self.context.load_resource(corner)
            )

        sprite.graphics = ContainerGraphics(
            sprite, tile_render=tile_render,
            border_images=border_images
        )

    def get_tile_render(self, file_name):
        tile = self.context.load_resource(file_name)
        sw, sh = self.context.game.screen.size
        sw *= 2
        sh *= 2

        return ContainerGraphics.tile_surface(
            tile, Image.get_surface((sw, sh))
        )

    def get_border_render(self, file_name, side):
        border_image = self.context.load_resource(file_name)
        bw, bh = border_image.get_size()
        sw, sh = self.context.game.screen.size
        sw *= 2
        sh *= 2

        t, l, r, b = con.SIDE_CHOICES
        size = {
            t: (sw, bh),
            l: (bw, sh)
        }[side]

        return ContainerGraphics.tile_surface(
            border_image, Image.get_surface(size)
        )


class UiInterface(UiGraphicsInterface):
    def set_member_sprites(self, sprite, table):
        members = MemberTable(table)
        members.map_to_members(self.get_item_as_sprite)
        sprite.set_members(members)

    def get_item_as_sprite(self, item):
        sprite = None

        if type(item) is str:
            sprite = UiSprite("Text sprite: {}".format(item))
            self.set_text(sprite, item)

        return sprite

    @staticmethod
    def drift(sprite):
        sprite.update_methods.append(
            lambda: sprite.move(1, 0, .25)
        )

    @staticmethod
    def grow(sprite):
        def grow_sprite(s):
            w, h = s.size
            s.set_size(w + 1, h + 1)

        sprite.update_methods.append(
            lambda: grow_sprite(sprite)
        )


class UiSprite(Sprite):
    def __init__(self, name):
        super(UiSprite, self).__init__(name)

        self.style = None

    def set_size(self, w, h):
        super(UiSprite, self).set_size(w, h)
        self.handle_event("change_size")

    def set_position(self, x, y):
        super(UiSprite, self).set_position(x, y)
        self.handle_event("change_position")


class ContainerSprite(UiSprite):
    def __init__(self, name):
        super(ContainerSprite, self).__init__(name)

        self.members = MemberTable()

    @property
    def member_list(self):
        return self.members.member_list

    def set_paused(self, value):
        super(ContainerSprite, self).set_paused(value)

        for sprite in self.member_list:
            sprite.set_paused(value)

    def set_visible(self, value):
        super(ContainerSprite, self).set_visible(value)

        for sprite in self.member_list:
            sprite.set_visible(value)

    def set_size(self, w, h):
        if self.style:
            w, h = self.members.adjust_size(
                (w, h), self.style.border_size,
                self.style.buffers
            )

        super(ContainerSprite, self).set_size(w, h)

    def set_members(self, table):
        self.members = table
        self.handle_event("change_members")

    def on_change_members(self):
        for sprite in self.member_list:
            sprite.set_group(self.group)

        self.set_size(*self.size)
        self.set_position(*self.position)

    def on_change_position(self):
        if self.member_list and self.style:
            self.members.set_member_positions(
                self.position, self.size,
                self.style.border_size,
                self.style.buffers,
                self.style.aligns
            )

    def on_change_size(self):
        if self.graphics:
            self.graphics.reset_image()

    def on_death(self):
        for sprite in self.member_list:
            sprite.handle_event("death")
