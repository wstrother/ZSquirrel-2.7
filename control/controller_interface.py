import zsquirrel.constants as con
import zsquirrel.control.controllers as cont
import zsquirrel.control.input_manager as im
from zsquirrel.control.command_inputs import CommandInput, CommandStep, CommandCondition
from zsquirrel.context import ApplicationInterface


class ControllerInterface(ApplicationInterface):
    DEVICES_DICT = {
        con.BUTTON: cont.Button,
        con.DPAD: cont.Dpad,
        con.DEVICE_TRIGGER: cont.Trigger,
        con.THUMB_STICK: cont.ThumbStick,
        con.BUTTON_MAP_KEY: im.ButtonMappingKey,
        con.BUTTON_MAP_BUTTON: im.ButtonMappingButton,
        con.BUTTON_MAP_AXIS: im.ButtonMappingAxis,
        con.BUTTON_MAP_HAT: im.ButtonMappingHat,
        con.AXIS_MAP: im.AxisMapping,
    }

    def __init__(self, *args):
        super(ControllerInterface, self).__init__(*args)

        self.init_order = [
            self.load_controllers.__name__,
            self.set_controller_commands.__name__
        ]

    def load_controllers(self, layer, *file_names):
        i = 1

        for file_name in file_names:
            name = "{} {}".format(file_name, i)
            try:
                controller = ControllerInterface.make_controller(
                    name, self.context.load_resource(file_name)
                )
                layer.set_controller(controller)

            except IOError:
                print("Unable to build controller: {}".format(file_name))

            i += 1

    # return a controller object from a json formatted devices dict
    @staticmethod
    def make_controller(name, devices):
        controller = cont.Controller(name)

        try:
            for d in devices:
                cls = ControllerInterface.get_device_class(d)

                mapping = ControllerInterface.get_mapping(d)
                device = cls(d[con.NAME])

                controller.add_device(
                    device, mapping
                )

            return controller

        except IndexError:
            raise IOError("Unable to build controller " + name)
        except AssertionError:
            raise IOError("Unable to build controller " + name)

    @staticmethod
    def get_device_class(d):
        return ControllerInterface.DEVICES_DICT[d[con.CLASS]]

    @staticmethod
    def get_mapping(d):
        def get_m(md):
            c = md[0]
            a = md[1:]

            return ControllerInterface.DEVICES_DICT[c](*a)

        if d[con.CLASS] in (con.BUTTON, con.DEVICE_TRIGGER):
            return get_m(d[con.MAPPING])

        if d[con.CLASS] == con.DPAD:
            return [
                get_m(d[direction]) for direction in con.UDLR
            ]

        if d[con.CLASS] == con.THUMB_STICK:
            return [
                get_m(d[axis]) for axis in con.AXES
                ]

    def add_command_condition(self, name, *args):
        args = list(args)
        for arg in args:
            if type(arg) is str:
                args[args.index(arg)] = self.get_value(arg)

        condition = CommandCondition(*args)
        self.context.set_value(name, condition)

        return condition

    def add_command_step(self, name, window, *conditions):
        conditions = list(conditions)
        for c in conditions:
            if type(c) is str:
                conditions[conditions.index(c)] = self.get_value(c)

        step = CommandStep(name, window, *conditions)
        self.context.set_value(name, step)

        return step

    def add_command_input(self, name, window, devices, *steps):
        steps = list(steps)
        for s in steps:
            if type(s) is str:
                steps[steps.index(s)] = self.get_value(s)

        command = CommandInput(name, devices, window, *steps)
        self.context.set_value(name, command)

        return command

    def set_controller_commands(self, layer, index, data):
        if type(data) is str:
            data = self.context.load_resource(data)

        controller = layer.controllers[index]

        conditions = data.get(con.CONDITIONS, [])
        steps = data.get(con.STEPS, [])
        commands = data.get(con.COMMANDS, [])

        for c in conditions:
            name, *args = c
            self.add_command_condition(name, *args)

        for s in steps:
            name, *args = s
            self.add_command_step(name, *args)

        for co in commands:
            name, *args = co
            command = self.add_command_input(name, *args)
            controller.add_command(command)
