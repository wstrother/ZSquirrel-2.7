from zsquirrel.ui.ui_interface import UiInterface, UiSprite, ContainerSprite


class MenusInterface(UiInterface):
    def set_menu(self, sprite, *members):
        self.set_member_sprites(sprite, *members)

        sprite.press_activate = lambda: self.press_activate(sprite)
        sprite.move_pointer = lambda: self.move_pointer(sprite)

    def get_item_as_sprite(self, item):
        name = str(item)
        if len(name) > 20:
            name = name[:20]

        if type(item) is str:
            sprite = OptionSprite(name)
            self.set_text(sprite, item)

            return sprite

        else:
            return super(MenusInterface, self).get_item_as_sprite(item)

    @staticmethod
    def press_activate(sprite):
        if sprite.controller:
            a = sprite.controller.get_device("A")

            return a.check()

    @staticmethod
    def move_pointer(sprite):
        move = (0, 0)
        if sprite.controller:
            dpad = sprite.controller.get_device("Dpad")

            if dpad.check():
                move = dpad.get_value()

        return move


class OptionSprite(UiSprite):
    def on_select(self):
        color = self.style.selected_color
        self.set_style({
            "font_color": color
        })
        self.graphics.set_text(
            self.graphics.text, self.style
        )

    def on_unselect(self):
        color = self.style.normal_color
        self.set_style({
            "font_color": color
        })
        self.graphics.set_text(
            self.graphics.text, self.style
        )

    def on_activate(self):
        pass


class BlockSprite(ContainerSprite):
    def __init__(self, name):
        super(BlockSprite, self).__init__(name)

        self.members.select_function = self.selectable

        self.last_option = None
        self.pointer_paused = False

        self.press_activate = None
        self.move_pointer = None

        self.update_methods.append(
            self.update_menu
        )

    @staticmethod
    def selectable(option):
        return bool(getattr(option, "on_select", False))

    @property
    def active_option(self):
        return self.members.active_member

    def update_menu(self):
        menu_ready = self.member_list and self.move_pointer and self.press_activate

        if menu_ready:

            if not self.pointer_paused:
                x, y = self.move_pointer()
                active = self.active_option

                if x == 1:
                    active.handle_event("next_state")

                if x == -1:
                    active.handle_event("prev_state")

                self.members.move_pointer(x, y)
                self.handle_select()
                self.handle_activate()
                self.handle_pointer()

                self.last_option = self.active_option

    def handle_select(self):
        active = self.active_option
        last = self.last_option

        if last != active:
            active.handle_event("select")

            if last:
                last.handle_event("unselect")

    def handle_activate(self):
        active = self.members.active_member

        if active and self.press_activate():
            active.queue_event("activate")

    def handle_pointer(self):
        active = self.active_option

        if not self.selectable(active):
            self.members.adjust_pointer()

            if active != self.active_option:
                self.active_option.handle_event("select")

    def on_pause_pointer(self):
        self.pointer_paused = not self.pointer_paused

    def add_member_listeners(self, member):
        super(BlockSprite, self).add_member_listeners(member)
        if hasattr(member, "on_activate"):
            member.add_listener({
                "name": "activate",
                "target": self,
                "response": {
                    "name": "activate",
                    "option": member
                }
            })

    def on_activate(self):
        e = self.event
        print(e["option"])
