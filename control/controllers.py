from zsquirrel.utils.cache_list import CacheList
from math import sqrt
import zsquirrel.constants as con


class Controller:
    """
    The Controller object represents a virtual blueprint for a set of input devices
    that will be used for a given game environment. It has a list of input device objects
    which produce input values for a given frame. All of that data is stored in a frame
    cache by the controller object.
    """
    def __init__(self, name):
        """
        Controller objects have a 'frames' attribute composed of a utils.meters.CacheList
        object. There is also a 'devices' list that corresponds to individual input devices
        that have been added to the controller, as well as a 'commands' dict that can be
        used to specify command inputs, or specific patterns of controller input that can
        be checked on a given frame.

        :param name: (str) hashable str that identifies a controller object for use in
            data serialization
        """
        self.name = name
        self.frames = CacheList(con.CONTROLLER_FRAME_DEPTH)

        self.devices = []
        self.commands = {}

    def add_device(self, device):
        """
        Adds an input device to the 'devices' list

        :param device: InputDevice subclass object
        """
        device.set_controller(self)
        self.devices.append(device)

    def get_device_index(self, name):
        """
        returns list index for a given device name. raises a ValueError
        if no input device is found with a matching name.

        :param name: (str) 'name' attribute of a given input device
        """
        for d in self.devices:
            if d.name == name:
                return self.devices.index(d)

        raise ValueError("no device with name {}".format(name))

    def get_device(self, name):
        """
        returns device object for a given device name

        :param name: (str) 'name' attribute of a given input device
        :return: InputDevice subclass object
        """
        return self.devices[
            self.get_device_index(name)
        ]

    def get_device_frames(self, name, depth=0):
        """
        returns a list with input data for a given device over previous frames.
        if the 'depth' parameter is set to 0, this method returns the entire
        previous frame cache for the device specified

        :param name: (str) 'name' attribute of a given input device
        :param depth: (int) number of previous frames to include
        :return: (list) a list containing input data for a given number
            of frames
        """
        output = []
        i = self.get_device_index(name)

        for frame in self.frames:
            output.append(frame[i])

        if depth:
            output = output[-depth:]

        return output

    def add_command(self, command):
        """
        Adds a CommandInput object to the 'commands' dict, using the
        command's 'name' attribute as the key

        :param command: controllers.command_inputs.CommandInput object
        """
        self.commands[command.name] = command

    def get_command_frames(self, device_names, depth=1):
        """
        This method returns a list of input data for various devices over
        previous frames. The output of this method is a nested list of tuples,
        where each item within a given tuple corresponds by index to the
        name passed in the 'device_names' parameter.

        e.g.:
            [(device_0, device_1),
            (device_0, device_1),
            (device_0, device_1)]

        :param device_names: ([str, str]) names of the relevant input
            devices
        :param depth: (int) amount of previous frames to return input from
        :return: (list) list of input data over a given amount of previous
            frames
        """
        frames = []

        for name in device_names:
            frames.append(
                self.get_device_frames(name, depth)
            )

        frames = list(zip(*[f for f in frames]))

        output = []
        for f in frames:
            line = []
            for d in f:
                if type(d) is tuple:
                    line += list(d)
                else:
                    line.append(d)
            output.append(tuple(line))

        return output

    def update(self):
        """
        This method updates the 'frames' CacheList with input data from each
        device in the 'devices' list, as well as calling each of their own
        update methods.

        It also calls the update method for each CommandInput object in the
        'commands' dict, using the 'get_command_frames' method for that
        object's specified devices
        """
        self.update_frames()

        for d in self.devices:
            d.update()

        for name in self.commands:
            command = self.commands[name]
            command.update(
                self.get_command_frames(command.devices)
            )

    def update_frames(self):
        """
        This method appends frame data to the 'frames' CacheList
        """
        frame = []

        for d in self.devices:
            frame.append(
                d.get_input()
            )

        self.frames.append(frame)


class InputDevice:
    """
    This abstract superclass defines the main methods of the input device object.
    Each device is paired with a controller object which is used to access the frame cache, and
    some devices have additional attributes that can be altered by the update method based on this
    data. Each device also defines a get_input method for producing frame data.
    """
    def __init__(self, name, mapping=None):
        """
        Each input device should be initialized with controllers.input_mapper.Mapping subclass
        object which provides methods for reporting input data to the Controller object
        set to the 'controller' attribute

        The 'default' attribute should define a default input value to be reported when
        an input value cannot otherwise be determined

        :param name: (str) hashable key for use with serialized data
        :param mapping: controllers.input_mapper.Mapping subclass object
        """
        self.name = name
        self.default = None
        self.controller = None
        self.mapping = mapping

    def __repr__(self):
        c = self.__class__.__name__
        n = self.name

        return "{}: '{}'".format(c, n)

    def set_controller(self, controller):
        """
        This method set's the 'controller' attribute

        :param controller: Controller object
        """
        self.controller = controller

    @property
    def last(self):
        """
        This method returns the input data from the previous frame,
        if less than 2 frames are in the 'controller' object's frame cache
        then the 'default' value is returned

        :return: input data from the previous frame
        """
        frames = self.get_frames()

        if len(frames) < 2:
            return self.default

        else:
            return frames[-2]

    def get_frames(self):
        """
        This method gets a list of input data as returned by the
        Controller.get_device_frames method for this specific input device

        :return: (list) input data for this specific input device
        """
        if self.controller:
            return self.controller.get_device_frames(self.name)

    def get_value(self):
        """
        This method gets the most recent value from the output of
        the 'get_frames' method

        :return: input data for the most recent frame returned by
            the 'get_frames' method
        """
        if self.get_frames():
            return self.get_frames()[-1]

        else:
            return self.default

    def update(self):
        pass

    def get_input(self):
        return self.default


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
    def __init__(self, name, mapping):
        """
        The 'init_delay' attribute is an int corresponding to the number of frames
        that a continuous button press input takes to register as repeated individual
        presses in certain contexts and the 'held_delay' attribute is an int that
        represents the frequency of regular inputs once the 'held_delay' threshold
        has been passed

        The 'held' attribute is an int representing the number of frames that a button
        has been pressed continuously for, and the 'lifted' attribute is a bool that
        represents whether the button is currently not held.

        :param name: (str) hashable key for use with serialized data
        :param mapping: controllers.input_mapper.Mapping subclass object
        """
        super(Button, self).__init__(name, mapping)

        self.init_delay = con.INIT_DELAY
        self.held_delay = con.HELD_DELAY
        self.held = 0
        self.default = 0
        self.lifted = False

    @property
    def ignore(self):
        """
        Returns a bool representing whether a continuously held button press should be
        ignored on a given frame in certain contexts

        :return: (bool) Whether the button press should be ignored
        """
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
        """
        Returns a bool representing whether a button press should be registered in contexts
        where a continuously held button press should not register on every individual frame

        :return: (bool) Whether the button press should register
        """
        return bool(self.held and not self.ignore)

    def is_held(self):
        """
        Returns True if the 'held' value is greater than 0

        :return: (bool)
        """
        return bool(self.held)

    # negative_edge returns True if a button was pushed the last frame and has just
    # been released. It returns False in all other cases.
    def negative_edge(self):
        """
        Returns True if a button was pushed the last frame and has just
        been released. It returns False in all other cases.

        :return: (bool)
        """
        frames = self.get_frames()
        current, last = frames[-1], frames[-2]

        return last and not current

    # FRAME DATA:
    # 0: button not pressed
    # 1: button pressed
    def get_input(self):
        """
        Returns the value of the mapping.is_pressed() method cast to an int (either 1 or 0)

        :return: (int) the input value is reported by the 'mapping' object
        """
        if self.mapping:
            return int(self.mapping.is_pressed())
        else:
            return super(Button, self).get_input()

    def update(self):
        """
        The update method assigns the value of the 'lifted' flag and the 'held' attribute
        """
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
    """
    def __init__(self, name, up, down, left, right):
        """
        The Dpad input device is initialized using 4 different Button objects as attributes
        corresponding the up, down, left, and right directions.

        The 'last_direction' attribute represents the last direction the Dpad was held in
        (the 'neutral' direction or (0, 0) is not considered a direction) and defaults to
        a value of (1, 0)

        :param name: (str) hashable key for use with serialized data
        :param up: Button object
        :param down: Button object
        :param left: Button object
        :param right: Button object
        """
        super(Dpad, self).__init__(name)
        self.last_direction = 1, 0
        self.default = 0, 0, 0, 0

        self.up = up
        self.down = down
        self.left = left
        self.right = right

    @property
    def buttons(self):
        """
        Returns a tuple of each direction button in the standard order of up, down, left, right

        :return: (tuple) of Button objects
        """
        return self.up, self.down, self.left, self.right

    @property
    def held(self):
        """
        Returns the 'held' attribute of whichever Button object in self.buttons has been held
        for the most frames

        :return: (bool)
        """
        return self.get_dominant().held

    # returns the direction button that has been held for the most frames
    def get_dominant(self):
        """
        The 'get_dominant' method is used by the 'check' method to set the 'ignore' flag based
        on the frame interval of whichever Dpad button has been held the longest.

        :return: Button object
        """
        u, d, l, r = self.buttons

        dominant = sorted([u, d, l, r], key=lambda b: b.held * -1)[0]

        return dominant

    def check(self):
        """
        Returns the output of the check() method on whichever Button object is returned
        by the get_dominant() method

        :return: (bool)
        """
        return self.get_dominant().check()

    # FRAME DATA:
    # (int) for each button in (up, down, left, right)
    def get_input(self):
        """
        Returns input data as a tuple of individual input data values for each Button object
        in self.buttons

        :return: (tuple) input data for each button
        """
        return tuple([b.get_input() for b in self.buttons])

    # 0, 0: neutral
    # +x, +y: right pushed / down pushed
    # -x, -y: left pushed / up pushed
    def get_value(self):
        """
        The get_value method returns the most recent input value as a tuple of ints that
        correspond to two directional axes (x, and y) each with a value of either
        -1, 0, or 1

        :return: (tuple (int, int)) directional value of the Dpad object
        """
        u, d, l, r = super(Dpad, self).get_value()

        x, y = 0, 0
        x -= int(l)
        x += int(r)
        y += int(d)
        y -= int(u)

        return x, y

    def update(self):
        """
        The update method calls the update method of each Button object in self.buttons
        as well as setting the the 'last_direction' attribute
        """
        for b in self.buttons:
            b.update()

        x, y = self.get_value()

        if (x, y) != (0, 0):
            self.last_direction = x, y


class ThumbStick(InputDevice):
    """
    The ThumbStick object represents an input device that has two axes (X and Y) yielding
    float values from -1.0 to 1.0 inclusive.

    """
    def __init__(self, name, x_axis, y_axis):
        """
        The 'dead_zone' parameter defines a float threshold beyond which an axis or direction
        can be considered to be 'pressed' in some contexts

        :param name: (str) hashable key for use with serialized data
        :param x_axis: controllers.input_mapper.AxisMapping object
        :param y_axis: controllers.input_mapper.AxisMapping object
        """
        super(ThumbStick, self).__init__(name)
        self.default = 0.0, 0.0
        self.dead_zone = con.STICK_DEAD_ZONE

        self.x_axis = x_axis
        self.y_axis = y_axis

    def get_magnitude(self):
        """
        This method returns a float that represents the total magnitude of a 2D displacement vector
        corresponding to the values of each axis

        :return: (float) total magnitude of displacement
        """
        x, y = self.x_axis, self.y_axis
        x **= 2
        y **= 2
        m = round(sqrt(x + y), 3)

        return m

    def is_neutral(self):
        """
        Returns a bool representing whether or not the stick is in a neutral position, with
        allowances for a total displacement up to the 'dead_zone' attribute value

        :return: (bool)
        """
        return self.get_magnitude() < self.dead_zone

    def check(self):
        """
        Returns the output of 'is_neutral'

        :return: (bool)
        """
        return not self.is_neutral()

    # 0, 0: neutral
    # +x, +y: right pushed / down pushed
    # -x, -y: left pushed / up pushed
    def get_input(self):
        """
        Returns a tuple of float values for each axis (x and Y)

        :return: (tuple (float, float)) input data for a given frame
        """
        x, y = self.x_axis.get_value(), self.y_axis.get_value()

        return x, y


class Trigger(InputDevice):
    """
    The Trigger object represents a single axis of displacement, with the input values
    represented as a single float between 0.0 and 1.0

    """
    def __init__(self, name, mapping):
        """
        The 'dead_zone' parameter defines a float threshold beyond which the input value
        of the trigger should register as 'pressed' in certain contexts

        :param name: (str) hashable key for use with serialized data
        :param mapping: controllers.input_mapper.AxisMapping subclass object
        """
        super(Trigger, self).__init__(name, mapping)
        self.default = 0.0
        self.dead_zone = con.STICK_DEAD_ZONE

    def check(self):
        """
        Returns True if the current input value is greater than the 'dead_zone' attribute
        :return: (bool)
        """
        return abs(self.get_value()) > self.dead_zone

    def get_input(self):
        """
        Returns the output of the AxisMapping object's get_value() method
        
        :return: (float)
        """
        return max(0.0, self.mapping.get_value())
