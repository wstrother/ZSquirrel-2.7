from control.input_manager import InputManager
import constants as con
from control.controller_interface import ControllerInterface


def build_controller(im, devices):
    return [build_device(im, device) for device in devices]


def build_device(im, device):
    cls = device[con.CLASS]

    if cls == con.THUMB_STICK:
        device = build_thumb_stick(im, device)

    if cls == con.BUTTON:
        device = build_button(im, device)

    if cls == con.TRIGGER:
        device = build_trigger(im, device)

    if cls == con.DPAD:
        device = build_dpad(im, device)

    return device


def build_thumb_stick(im, device):
    x_mapping = im.get_axis()
    y_mapping = im.get_axis()
    device[con.X_AXIS] = x_mapping.get_args()
    device[con.Y_AXIS] = y_mapping.get_args()

    return device


def build_dpad(im, device):
    u_mapping = im.get_mapping()
    d_mapping = im.get_mapping()
    l_mapping = im.get_mapping()
    r_mapping = im.get_mapping()

    device[con.UP] = u_mapping.get_args()
    device[con.DOWN] = d_mapping.get_args()
    device[con.LEFT] = l_mapping.get_args()
    device[con.RIGHT] = r_mapping.get_args()

    return device


def build_button(im, device):
    mapping = im.get_mapping()
    device[con.MAPPING] = mapping.get_args()

    return device


def build_trigger(im, device):
    mapping = im.get_axis()
    device[con.MAPPING] = mapping.get_args()

    return device


if __name__ == "__main__":
    manager = InputManager()
    profile = [
        {"name": "Start", "class": "button"},
        {"name": "Dpad", "class": "dpad"},
        {"name": "Stick", "class": "thumb_stick"},
        {"name": "A", "class": "button"}
    ]

    i = 0
    for d in profile:
        print("Choose input for {}".format(d["name"]))
        profile[i] = build_device(manager, d)
        i += 1

    for d in profile:
        print(d)
