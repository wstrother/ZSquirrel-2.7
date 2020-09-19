import zsquirrel.constants as con
import pygame


class ZsInputError(Exception):
    pass


pygame.init()

INPUT_DEVICES = {}


def get_device_key(joy):
    return "{} {}".format(joy.get_name(), joy.get_id())


for J in range(pygame.joystick.get_count()):
    JOY = pygame.joystick.Joystick(J)
    JOY.init()
    INPUT_DEVICES[get_device_key(JOY)] = JOY


class Mapping:
    def __init__(self, name, id_num):
        self.name = name
        self.id_num = id_num
        self.map_type = ""
        self.joy_device_name = ""

    def __repr__(self):
        return "{}".format(self.get_json())

    def get_json(self):
        return {
            con.NAME: self.name,
            con.ID_NUM: self.id_num,
            con.MAP_TYPE: self.map_type
        }

    def get_device(self):
        try:
            return INPUT_DEVICES[self.joy_device_name]
        except KeyError:
            raise ZsInputError("Input Device '{}' is not connected".format(
                self.joy_device_name
            ))


class ButtonMappingKey(Mapping):
    def __init__(self, name, id_num):
        if type(id_num) is str:
            id_num = self.get_id(id_num)
        super(ButtonMappingKey, self).__init__(name, id_num)

        self.map_type = con.BUTTON_MAP_KEY

    def is_pressed(self):
        return pygame.key.get_pressed()[self.id_num]

    def get_key_name(self):
        return pygame.key.name(self.id_num)

    @staticmethod
    def get_id(key_string):
        if len(key_string) > 1:
            key = con.K_ + key_string.upper()
        else:
            key = con.K_ + key_string

        return pygame.__dict__[key]

    def get_value(self):
        return self.is_pressed()


class ButtonMappingButton(ButtonMappingKey):
    def __init__(self, name, id_num, joy_name):
        super(ButtonMappingButton, self).__init__(name, id_num)
        self.joy_device_name = joy_name

        self.map_type = con.BUTTON_MAP_BUTTON

    def get_json(self):
        d = super(ButtonMappingButton, self).get_json()
        d[con.JOY_DEVICE] = self.joy_device_name

        return d

    def is_pressed(self):
        return self.get_device().get_button(self.id_num)


class ButtonMappingAxis(ButtonMappingButton):
    def __init__(self, name, id_num, joy_name, sign):
        super(ButtonMappingAxis, self).__init__(name, id_num, joy_name)
        self.sign = sign

        self.map_type = con.BUTTON_MAP_AXIS

    def get_json(self):
        d = super(ButtonMappingAxis, self).get_json()
        d[con.SIGN] = self.sign

        return d

    def is_pressed(self):
        axis = self.get_device().get_axis(self.id_num)

        return axis * self.sign > con.STICK_DEAD_ZONE


class ButtonMappingHat(ButtonMappingButton):
    def __init__(self, name, id_num, joy_name, position, axis, diagonal):
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
        hat = self.get_device().get_hat(self.id_num)

        if not self.diagonal:
            return hat[self.axis] == self.position[self.axis]
        else:
            return hat == self.position


class AxisMapping(Mapping):
    def __init__(self, name, id_num, joy_name, sign):
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
        sign = self.sign

        return self.get_device().get_axis(self.id_num) * sign


class InputMapper:
    def __init__(self):
        self.axis_neutral = False
        self.axis_min = con.AXIS_MIN
        self.devices = INPUT_DEVICES

    def check_axes(self, devices):
        axes = []
        for device in devices:
            for i in range(device.get_numaxes()):
                axes.append(device.get_axis(i))

        if not self.axis_neutral:
            self.axis_neutral = all([axis < self.axis_min for axis in axes])

    def get_button(self, name):
        devices = list(self.devices.values())
        pygame.event.clear()
        mapping = None

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
        pygame.event.clear()
        mapping = None
        devices = list(self.devices.values())

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
