from ui.ui_interface import UiInterface, UiSprite
from utils.cache_list import CacheList
# from control.controllers import Button, Dpad, ThumbStick, Trigger


class HudInterface(UiInterface):
    def set_controller_hud(self, sprite, layer, index):
        controller = layer.controllers[index]
        devices = controller.devices

        table = []
        for d in devices:
            row = [d.name, [self.get_hud_sprite(d, "get_value")]]
            table.append(row)

        self.set_member_sprites(sprite, *table)

    def set_member_huds(self, sprite, *huds):
        hud_sprites = [self.get_hud_sprite(*hud) for hud in huds]
        members = [[h] for h in hud_sprites]
        self.set_member_sprites(sprite, *members)

    def get_hud_sprite(self, target, attr, *args):
        name = "{} - {}".format(target.name, attr)

        size = 1
        if len(args) > 0:
            size = args[0]

        rate = 12
        if len(args) > 1:
            rate = args[1]

        maximum = 10
        if len(args) > 2:
            maximum = args[2]

        sprite = HudSprite(name, size, rate)
        sprite.set_value_func(
            self.get_attr_func(target, attr)
        )

        if "average" in args:
            sprite.set_cache_func(sprite.get_cache_average)

        if "changes" in args:
            sprite.set_cache_func(
                lambda: sprite.get_cache_changes(maximum)
            )

        self.set_text(sprite, "")

        return sprite

    @staticmethod
    def get_attr_func(target, attr):
        if callable(attr):
            return attr

        elif callable(getattr(target, attr)):
            return getattr(target, attr)

        else:
            return lambda: getattr(target, attr)


class HudSprite(UiSprite):
    def __init__(self, name, cache_size, refresh_rate):
        super(HudSprite, self).__init__(name)

        self.cache = CacheList(cache_size)
        self.rate = refresh_rate
        self.last_change = 0
        self.get_value = None
        self.get_cache = self.get_cache_latest

        self.update_methods += [
            self.update_cache,
            self.update_hud_text
        ]

    def set_value_func(self, func):
        self.get_value = func

    def set_cache_func(self, func):
        self.get_cache = func

    def format_text(self, value):
        if type(value) in (int, float, str, bool):
            return "{}".format(value)

        elif type(value) is float:
            return "{:1.5}".format(value)

        elif type(value) is tuple:
            return "({})".format(
                ", ".join([self.format_text(i) for i in value])
            )

        elif type(value) is list:
            return [self.format_text(i) for i in value]

        else:
            return ""

    def get_cache_latest(self):
        if self.cache:
            return self.cache[-1]

    def get_cache_average(self):
        return self.cache.average()

    def get_cache_changes(self, maximum):
        return self.cache.changes(maximum)

    def get_cache_change_func(self, depth):
        return lambda: self.get_cache_changes(depth)

    def update_cache(self):
        if self.get_value:
            self.cache.append(self.get_value())

    def update_hud_text(self):
        if self.graphics and self.last_change == 0:
            self.last_change = self.rate
            old = self.graphics.text
            new = self.format_text(self.get_cache())

            if old != new:
                self.graphics.set_text(new, self.style)
                self.handle_event("change_text")

        self.last_change -= 1
