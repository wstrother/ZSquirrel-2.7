import constants as con
import control.controllers as cont
import control.input_manager as im
from context import ApplicationInterface


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
