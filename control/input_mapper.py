import zsquirrel.constants as con
import pygame

'''
This module defines a set of classes that allow mappings of certain inputs using Pygame's joystick/keyboard
events API to the InputDevice subclasses as defined in ZSquirrel's controllers.py module.

The Pygame joystick module is initialized when this module is imported, and the InputMapper class provides
methods that creates Mapping objects which correspond to individual Joystick events 
(JOYAXISMOTION, JOYBUTTONDOWN, JOYHATMOTION) as well as the KEYDOWN event to be used by the 
InputDevice.get_input() method.

The Mapping object class also provides a method for returning a JSON hashable dict object that can be used
to serialize the parameters used to initialize it, such that those arguments can be used to generate
Mappings for InputDevice objects by loading data through an ApplicationInterface object.

Four different Mapping subclasses (ButtonMappingKey, ButtonMappingButton, ButtonMappingHat, and
ButtonMappingAxis) can be used as mappings to yield input for any controllers.Button object (and
controllers.Dpad implicitly), and one Mapping subclass (AxisMapping) is used to yield input for
the controllers.ThumbStick and controllers.Trigger objects.

The controllers.Button object will require only one Mapping subclass object to yield input, but
controllers.Dpad will require four (corresponding to up, down, left, right respectively), which
will auotmatically be instantiated as their own controllers.Button objects.

The controllers.Axis object will require two AxisMapping objects to yield input (for the x and y axes
respectively), while controllers.Trigger will require only one.

'''


class ZsInputError(Exception):
    pass


pygame.init()

INPUT_DEVICES = {}


def get_device_key(joy):
    """
    This method returns a Pygame Joystick object as a hashable key (a String)

    :param joy: pygame.joystick.Joystick() object
    :return: str: a hashable data key that corresponds to that Joystick device
    """
    return "{} {}".format(joy.get_name(), joy.get_id())


for J in range(pygame.joystick.get_count()):
    JOY = pygame.joystick.Joystick(J)
    JOY.init()
    INPUT_DEVICES[get_device_key(JOY)] = JOY


class Mapping:
    """
    This superclass defines basic methods for each type of Mapping subclass object.
    It should not be instantiated directly.
    """
    def __init__(self, name, id_num):
        """
        The init method defines some hashable attributes that are used to serialize
        the Mapping object's paramters as JSON data, including the name of the
        corresponding InputDevice object, the type of Mapping subclass that is
        expected, and where applicable, the name and ID number of the USB joystick
        device.

        :param name: (str) hashable key corresponding to an InputDevice object
        :param id_num: (int) used by Pygame.joystick to identify the corresponding
            USB joystick device
        """
        self.name = name
        self.id_num = id_num
        self.map_type = ""
        self.joy_device_name = ""

    def __repr__(self):
        return "{}".format(self.get_json())

    def get_json(self):
        """
        Returns the Mapping object's parameters as a JSON hashable dict object

        :return: (dict) a JSON hashable dict object
        """
        return {
            con.NAME: self.name,
            con.ID_NUM: self.id_num,
            con.MAP_TYPE: self.map_type
        }

    def get_device(self):
        """
        Returns the corresponding USB joystick device as initialized by the
        pygame joystick module, or raises a ZsInputError if the corresponding
        device is not detected.

        If joy_device_name is an empty string, it is assumed the mapping goes
        to the keyboard, and None is returned.

        :return: pygame.joystick.Joystick object
        """
        if self.joy_device_name:
            try:
                return INPUT_DEVICES[self.joy_device_name]
            except KeyError:
                raise ZsInputError("Input Device '{}' is not connected".format(
                    self.joy_device_name
                ))


class ButtonMappingKey(Mapping):
    """
    This Mapping subclass corresponds to a keyboard key and returns a bool
    for whether or not this key is being pressed, to be used by InputDevice.get_input()
    """
    def __init__(self, name, id_num):
        """

        :param name: (str) corresponding name of InputDevice object
        :param id_num: (int) used as index to identify the specific
            keyboard key returned by pygame.key.get_pressed()
        """
        if type(id_num) is str:
            id_num = self.get_id(id_num)
        super(ButtonMappingKey, self).__init__(name, id_num)

        self.map_type = con.BUTTON_MAP_KEY

    def is_pressed(self):
        """

        :return: (bool) returns a bool corresponding to whether or not
            the key is pressed
        """
        return pygame.key.get_pressed()[self.id_num]

    def get_key_name(self):
        """

        :return: (str) returns the name of the corresponding key
        """
        return pygame.key.name(self.id_num)

    @staticmethod
    def get_id(key_string):
        """
        Static method used to obtain the correct index for a given key
        to identify that key's corresponding output from the
        pygame.key.get_pressed() method

        :param key_string: (str) the key constant as defined by pygame
        :return:
        """
        if len(key_string) > 1:
            key = con.K_ + key_string.upper()
        else:
            key = con.K_ + key_string

        return pygame.__dict__[key]


class ButtonMappingButton(ButtonMappingKey):
    """
    This Mapping subclass corresponds to a button on an associated USB joystick
    device and is used to yield input for the controllers.Button object
    """
    def __init__(self, name, id_num, joy_name):
        """

        :param name: (str) corresponding name of InputDevice object
        :param id_num: (int) used as an argument to identify the specific
            joystick button returned by pygame.joystick.Joystick.get_pressed()
        :param joy_name: (str) the USB joystick identifier as defined by
            the pygame.event.joy attribute
        """
        super(ButtonMappingButton, self).__init__(name, id_num)
        self.joy_device_name = joy_name

        self.map_type = con.BUTTON_MAP_BUTTON

    def get_json(self):
        d = super(ButtonMappingButton, self).get_json()
        d[con.JOY_DEVICE] = self.joy_device_name

        return d

    def is_pressed(self):
        """

        :return: (bool) Whether or not the button is currently pressed
        """
        return self.get_device().get_button(self.id_num)


class ButtonMappingAxis(ButtonMappingButton):
    """
    This Mapping sublcass allows a JOYAXISMOTION event to yield input for a
    controllers.Button object
    """
    def __init__(self, name, id_num, joy_name, sign):
        """

        :param name: (str) corresponding name of InputDevice object
        :param id_num: (int) used as an argument to identify the specific
            joystick axis returned by pygame.joystick.Joystick.get_axis()
        :param joy_name: (str) the USB joystick identifier as defined by
            the pygame.event.joy attribute
        :param sign: (int) either 1 or -1, used to determine which direction
            the axis should be extended in to read as True when returned
            by the is_pressed() method
        """
        super(ButtonMappingAxis, self).__init__(name, id_num, joy_name)
        self.sign = sign

        self.map_type = con.BUTTON_MAP_AXIS

    def get_json(self):
        d = super(ButtonMappingAxis, self).get_json()
        d[con.SIGN] = self.sign

        return d

    def is_pressed(self):
        """
        Used to convert a JOYAXISMOTION event into binary input for the
        controllers.Button.get_input() method

        the pygame.constants.STICK_DEAD_ZONE value determines the minimum
        amount that an axis should be extended before it registers as
        being "pressed" when mapped to a button

        :return: (bool) whether the axis value is moved in the direction
        corresponding to the sign attribute
        """
        axis = self.get_device().get_axis(self.id_num)

        return axis * self.sign > con.STICK_DEAD_ZONE


class ButtonMappingHat(ButtonMappingButton):
    """
    This Mapping subclass allows a JOYHATMOTION event to yield input for a
    controllers.Button object
    """
    def __init__(self, name, id_num, joy_name, position, axis, diagonal):
        """

        :param name: (str) corresponding name of InputDevice object
        :param id_num: (int) used as an argument to identify the specific
            joystick hat returned by pygame.joystick.Joystick.get_hat()
        :param joy_name: (str) the USB joystick identifier as defined by
            the pygame.event.joy attribute
        :param position: (tuple (int, int)) the tuple value returned by
            pygame.joystick.Joystick.get_hat() used to determine when
            the is_pressed() method returns True
        :param axis: (int) identifies an index within the tuple returned
            by pygame.joystick.Joystick.get_hate() that should be checked
            against in the is_pressed() method
        :param diagonal: (bool) a flag to determine whether both axes
            need to be checked by the is_pressed() method
        """
        super(ButtonMappingHat, self).__init__(name, id_num, joy_name)
        self.position = position
        self.axis = axis
        self.diagonal = diagonal

        self.map_type = con.BUTTON_MAP_HAT

    def get_json(self):
        d = super(ButtonMappingHat, self).get_json()
        d[con.AXIS] = self.axis
        d[con.DIAGONAL] = self.diagonal
        d[con.POSITION] = self.position

        return d

    def is_pressed(self):
        """
        By default, only one axis of the hat position is checked, but if the
        diagonal flag is set, both axes must correspond to the correct
        position or else, False will be returned

        :return: (bool) whether the hat position corresponds to the correct
            value to return True
        """
        hat = self.get_device().get_hat(self.id_num)

        if not self.diagonal:
            return hat[self.axis] == self.position[self.axis]
        else:
            return hat == self.position


class AxisMapping(Mapping):
    """
    This Mapping subclass allows a JOYAXISMOTION event to yield input for
    a controllers.ThumbStick or controllers.Trigger object.

    """
    def __init__(self, name, id_num, joy_name, sign):
        """

        :param name: (str) corresponding name of InputDevice object
        :param id_num: (int) used as an argument to identify the specific
            joystick axis returned by pygame.joystick.Joystick.get_axis()
        :param joy_name: (str) the USB joystick identifier as defined by
            the pygame.event.joy attribute
        :param sign: (int) (1 or -1) a multiplier used to determine whether
            the effective input range should be flipped relative to the
            pygame.event JOYAXISMOTION.value attribute
        """
        super(AxisMapping, self).__init__(name, id_num)
        self.sign = sign
        self.joy_device_name = joy_name

        self.map_type = con.AXIS_MAP

    def get_json(self):
        d = super(AxisMapping, self).get_json()
        d[con.SIGN] = self.sign
        d[con.JOY_DEVICE] = self.joy_device_name

        return d

    def get_value(self):
        """
        Returns a value corresponding to the displacement of the axis

        :return: (float) a float value between -1 and 1
        """
        sign = self.sign

        return self.get_device().get_axis(self.id_num) * sign


class InputMapper:
    """
    This class provides methods that can be used to generate Mapping subclass objects
    for instantiating controllers.InputDevice subclass objects.
    """
    def __init__(self):
        """
        The axis_neutral flag is used by the check_axes() methods while listening for
        pygame.event objects so that JOYAXISMOTION events will not be detected as input
        when the get_button() and get_axis() methods initialize their 'listening' while loops

        The axis_min attribute is defined by zsquirrel.constants.AXIS_MIN as the minimum
        amount that an axis should be extended before registering as input within the
        'listening' loop of the get_button() and get_axis() methods
        """
        self.axis_neutral = False
        self.axis_min = con.AXIS_MIN

    def check_axes(self, devices):
        """
        Checks whether all axes on all connected USB joystick devices are set to neutral

        :param devices: (list) pygame.joystick.Joystick() objects
        :return: (bool) returns False unless all axes on all USB joystick devices within
            the devices list
        """
        axes = []
        for device in devices:
            for i in range(device.get_numaxes()):
                axes.append(device.get_axis(i))

        if not self.axis_neutral:
            self.axis_neutral = all([axis < self.axis_min for axis in axes])

    def get_button(self, name):
        """
        This method generates a mapping object by listening for certain events returned
        by the pygame.event.get() method. It generates a Mapping subclass object that
        should be used to yield input for a controllers.Button object's get_input() method

        :param name: (str) hashable name for controllers.Button object
        :return: (Mapping subclass object) initialized based on the input event detected
        """
        devices = list(INPUT_DEVICES.values())
        pygame.event.clear()
        mapping = None

        # 'listening' for input events
        while True:
            self.check_axes(devices)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()

                axis, button, hat, key = (
                    event.type == pygame.JOYAXISMOTION,
                    event.type == pygame.JOYBUTTONDOWN,
                    event.type == pygame.JOYHATMOTION,
                    event.type == pygame.KEYDOWN
                )

                if key:
                    mapping = ButtonMappingKey(name, event.key)

                if axis or button or hat:
                    device = devices[event.joy]

                    if axis and abs(event.value) > self.axis_min:
                        mapping = self.get_button_axis(name, device, event)

                    if button:
                        mapping = ButtonMappingButton(
                            name, event.button, get_device_key(device)
                        )

                    if hat and event.value != (0, 0):
                        mapping = self.get_button_hat(name, device, event)

                if mapping:
                    return mapping

    def get_button_axis(self, name, device, event):
        """
        This method is called by get_button when the JOYAXISMOTION event is
        detected, and returns a ButtonMappingAxis object to be used for
        yielding input to a controllers.Button object's get_input() method

        :param name: (str) name as passed by get_button()
        :param device: (str) pygame.event.joy attribute
        :param event: (pygame.event object)
        :return: ButtonMappingAxis() object
        """
        positive = event.value > 0
        sign = (int(positive) * 2) - 1

        if self.axis_neutral:
            self.axis_neutral = False

            return ButtonMappingAxis(
                name, event.axis,
                get_device_key(device), sign
            )

    @staticmethod
    def get_button_hat(name, device, event):
        """
        This method is called by get_button when the JOYHATMOTION event is
        detected, and returns a ButtonMappingHat object to be used for
        yielding input to a controllers.Button object's get_input() method

        :param name: (str) name as passed by get_button()
        :param device: (str) pygame.event.joy attribute
        :param event: (pygame.event object)
        :return: ButtonMappingHat() object
        """
        x, y = event.value
        axis, diagonal = 0, False

        if y != 0 and x == 0:
            axis = 1
        elif x != 0 and y != 0:
            diagonal = True

        return ButtonMappingHat(
            name, event.hat, get_device_key(device),
            (x, y), axis, diagonal=diagonal
        )

    def get_axis(self, name):
        """
        This method generates a mapping object by listening for JOYAXISMOTION events returned
        by the pygame.event.get() method. It generates a AxisMapping object that
        should be used to yield input for a controllers.ThumbStick or controllers.Trigger
        object's get_input() method

        :param name: (str) hashable name for controllers.ThumbStick or controllers.Trigger object
        :return: (AxisMapping() object) initialized based on the input event detected
        """
        pygame.event.clear()
        mapping = None
        devices = list(INPUT_DEVICES.values())

        # 'listening' for input events
        while True:
            self.check_axes(devices)

            for event in pygame.event.get():
                if event.type == pygame.JOYAXISMOTION and abs(event.value) > self.axis_min:

                    positive = event.value > 0
                    sign = (int(positive) * 2) - 1
                    id_num = event.axis
                    device = devices[event.joy]

                    if self.axis_neutral:
                        self.axis_neutral = False
                        joy_name = get_device_key(device)

                        mapping = AxisMapping(
                            name, id_num, joy_name, sign
                        )

                    if mapping:
                        return mapping
