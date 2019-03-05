from ui.ui_interface import UiInterface, UiSprite


class HudInterface(UiInterface):
    def set_controller_interface(self, sprite, layer, index):
        # controller = layer.controllers[index]
        pass

    def set_member_huds(self, sprite, *huds):
        hud_sprites = []

        for hud in huds:
            target, attr = hud
            name = "{} - {}".format(target.name, attr)
            hud_sprite = UiSprite(name)
            self.set_sprite_hud(hud_sprite, target, attr)
            hud_sprites.append(hud_sprite)

        members = [[h] for h in hud_sprites]
        self.set_member_sprites(sprite, *members)

    def set_sprite_hud(self, sprite, target, attr):
        self.set_text(sprite, "")
        sprite.update_methods.append(
            self.get_hud_update_method(sprite, target, attr)
        )

    def get_hud_update_method(self, sprite, target, attr):
        return lambda: self.update_hud_text(
            sprite,
            lambda: self.get_attr_text(target, attr)
        )

    @staticmethod
    def update_hud_text(sprite, get_text):
        old = sprite.graphics.text
        new = get_text()
        if old != new:
            sprite.graphics.set_text(get_text(), sprite.style)
            sprite.handle_event("change_text")

    @staticmethod
    def get_attr_text(target, attr):
        value = getattr(target, attr)

        return str(value)
