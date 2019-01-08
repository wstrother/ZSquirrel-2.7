from math import sqrt

from zs_constants import ControllerInputs as ConIn
from zs2.collections import CacheList


#
# Virtual controller / input device objects
#

class Controller:
    """
    The Controller object represents a virtual blueprint for a set of input devices
    that will be used for a given game environment. It has a list of input device objects
    and a mapping dictionary that pairs each device with a mapping object that produces the
    input value for a given frame. All of that data is stored in a frame cache by the controller
    object.
    """
    def __init__(self, name):
        self.name = name
        self.frames = CacheList(ConIn.CONTROLLER_FRAME_DEPTH)

        self.devices = []
        self.mappings = {}

    def __repr__(self):
        c = self.__class__.__name__
        n = self.name

        return "{}: '{}'".format(c, n)

    # returns list index for a given device name
    def get_device_index(self, name):
        for d in self.devices:
            if d.name == name:
                return self.devices.index(d)

        raise ValueError("no device with name {}".format(name))

    # returns device object for a given device name
    def get_device(self, name):
        return self.devices[
            self.get_device_index(name)
        ]

    # returns a frame cache with data for a given device
    def get_device_frames(self, name):
        output = []
        i = self.get_device_index(name)

        for frame in self.frames:
            output.append(frame[i])

        return output

    # add a device / input mapping to the controller object
    def add_device(self, device, mapping):
        device.controller = self
        self.mappings[device.name] = mapping
        self.devices.append(device)

        if type(device) is Dpad:
            # a Dpad input device is made up of four button devices

            buttons = device.make_d_buttons()
            for i in range(4):
                self.add_device(buttons[i], mapping[i])

    def remap_device(self, device_name, mapping):
        self.mappings[device_name] = mapping

    # update frame input data and call device update methods
    def update(self):
        self.update_frames()

        for d in self.devices:
            d.update()

        # self.command_manager.update()

    # append frame data to frame cache object
    def update_frames(self):
        frame = []

        for d in self.devices:
            m = self.mappings[d.name]

            frame.append(
                d.get_input(m)
            )

        self.frames.append(frame)

    def get_cfg(self):
        devices = {}

        for device in self.devices:
            devices[device.name] = self.get_device_cfg(device)

        return {self.name: {
            "devices": devices
        }}

    @staticmethod
    def get_device_cfg(device):
        d = {}
        class_dict = {
            Button: "button",
            Dpad: "dpad",
            ThumbStick: "thumb_stick",
            Trigger: "trigger"
        }
        d["class"] = class_dict[device.__class__]

        if d["class"] in ("button", "trigger"):
            d["mapping"] = str(device.mapping)

        if d["class"] == "dpad":
            d["up"] = str(device.up)
            d["left"] = str(device.left)
            d["down"] = str(device.down)
            d["right"] = str(device.right)

        if d["class"] == "thumb_stick":
            d["x_axis"] = str(device.x_axis)
            d["y_axis"] = str(device.y_axis)

        return d


class InputDevice:
    """
    This abstract superclass defines the main methods of the input device object.
    Each device is paired with a controller object which is used to access the frame cache, and
    some devices have additional attributes that can be altered by the update method based on this
    data. Each device also defines a get_input method for producing frame data.
    """
    def __init__(self, name):
        self.name = name
        self.default = None
        self.controller = None

    def __repr__(self):
        c = self.__class__.__name__
        n = self.name

        return "{}: '{}'".format(c, n)

    # get frame cache for this device
    def get_frames(self):
        if self.controller:
            return self.controller.get_device_frames(self.name)

    # get most recent value from frame cache
    def get_value(self):
        if self.get_frames():
            return self.get_frames()[-1]

        else:
            return self.default

    def update(self):
        pass

    @staticmethod
    def get_input(mapping):
        return int(mapping.is_pressed())


class Button(InputDevice):
    """
    A Button object corresponds to a single button input device. This class
    defines a number of extra attributes and methods that can make controller
    interfacing more useful, such as a negative_edge check method and a check
    method with a built in modular ignore-frame dampener for continuous button
    presses.
    Button objects have a 'held' attribute that records the number of frames the
    button has been continuously held.
    """
    def __init__(self, name):
        super(Button, self).__init__(name)

        self.init_delay = ConIn.INIT_DELAY
        self.held_delay = ConIn.HELD_DELAY
        self.held = 0
        self.default = 0
        self.lifted = False

    # ignore / check give a method for getting discrete input intervals from a
    # continuous button push.
    # See zs_constants.py to adjust INIT_DELAY and HELD_DELAY values
    @property
    def ignore(self):
        if not self.lifted:
            return True

        ignore = False
        h, i_delay, h_delay = (self.held,
                               self.init_delay,
                               self.held_delay)

        if 1 < h < i_delay:
            ignore = True
        elif h >= i_delay:
            if (h - i_delay) % h_delay != 0:
                ignore = True

        return ignore

    def check(self):
        return bool(self.held and not self.ignore)

    # negative_edge returns True if a button was pushed the last frame and has just
    # been released. It returns False in all other cases.
    def negative_edge(self):
        frames = self.get_frames()
        current, last = frames[-1], frames[-2]

        return last and not current

    # FRAME DATA:
    # 0: button not pressed
    # 1: button pressed
    @staticmethod
    def get_input(mapping):
        return int(mapping.is_pressed())

    def update(self):
        if not self.lifted and not self.get_value():
            self.lifted = True

        if self.get_value():
            self.held += 1
        else:
            self.held = 0


class Dpad(InputDevice):
    """
    A Dpad object represents an input device that can input 8 discrete directions through
    a combination of four individual buttons, one for up, down, left, and right.
    The 'get_dominant' method is used by the 'check' method to set the 'ignore' flag based
    on the frame interval of whichever Dpad button has been held the longest.
    Dpad objects have a 'last_direction' attribute that defaults to right (1, 0).
    """
    def __init__(self, name):
        super(Dpad, self).__init__(name)
        self.last_direction = (1, 0)
        self.default = (0, 0)

    def get_d_button(self, direction):
        if self.controller:
            return self.controller.get_device(
                self.name + "_" + direction
            )

        else:
            print("WARNING: no controller set for {}".format(self))

    def make_d_buttons(self):
        buttons = []

        for direction in ConIn.UDLR:
            name = self.name + "_" + direction
            buttons.append(
                Button(name)
            )

        return buttons

    @property
    def up(self):
        return self.get_d_button("up")

    @property
    def down(self):
        return self.get_d_button("down")

    @property
    def left(self):
        return self.get_d_button("left")

    @property
    def right(self):
        return self.get_d_button("right")

    @property
    def buttons(self):
        return [
            self.up,
            self.down,
            self.left,
            self.right
        ]

    @property
    def held(self):
        return self.get_dominant().held

    # returns the same thing as 'get_value'
    def get_direction(self):
        return self.get_value()

    # returns the direction button that has been held for the most frames
    def get_dominant(self):
        u, d, l, r = self.buttons

        dominant = sorted([u, d, l, r], key=lambda b: b.held * -1)[0]

        return dominant

    def check(self):
        return self.get_dominant().check()

    # FRAME DATA:
    # 0, 0: neutral
    # +x, +y: right pushed / down pushed
    # -x, -y: left pushed / up pushed
    @staticmethod
    def get_input(mappings):
        u, d, l, r = [m.is_pressed() for m in mappings]

        x, y = 0, 0
        x -= int(l)
        x += int(r)
        y += int(d)
        y -= int(u)

        return x, y

    def update(self):
        x, y = self.get_value()

        if (x, y) != (0, 0):
            self.last_direction = x, y


class ThumbStick(InputDevice):
    def __init__(self, name):
        super(ThumbStick, self).__init__(name)
        self.default = 0.0, 0.0
        self.dead_zone = ConIn.STICK_DEAD_ZONE

    @property
    def x_axis(self):
        return self.get_value()[0]

    @property
    def y_axis(self):
        return self.get_value()[1]

    def get_direction(self):
        return self.get_value()

    def get_magnitude(self):
        x, y = self.x_axis, self.y_axis
        x **= 2
        y **= 2
        m = round(sqrt(x + y), 3)

        return m

    def is_neutral(self):
        return self.get_magnitude() < self.dead_zone

    def check(self):
        return not self.is_neutral()

    @staticmethod
    def get_input(mappings):
        x, y = [m.get_value() for m in mappings]

        return x, y


class Trigger(InputDevice):
    def __init__(self, name):
        super(Trigger, self).__init__(name)
        self.default = 0.0
        self.dead_zone = ConIn.STICK_DEAD_ZONE

    def get_displacement(self):
        return self.get_value()

    def check(self):
        return self.get_value() > self.dead_zone

    @staticmethod
    def get_input(mapping):
        return mapping.get_value()
