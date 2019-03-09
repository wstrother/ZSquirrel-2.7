from animations.animations import Animation, AnimationLayer, AnimationStep, AnimationMachine
from geometry import Rect
from graphics import ImageSectionGraphics, GraphicsInterface
from utils.meters import Meter


class AnimationInterface(GraphicsInterface):
    def __init__(self, *args):
        super(AnimationInterface, self).__init__(*args)

        self.init_order += [
            self.set_animations.__name__,
            self.set_animation_machine.__name__
        ]

    def set_animation_machine(self, entity, data_file):
        data = self.context.load_resource(data_file)

        states = self.get_states_dict(entity, data)
        machine = AnimationMachine(entity, states)

        entity.update_methods.append(machine.update)
        entity.graphics.get_state = machine.get_state
        machine.set_state("default")

    def get_states_dict(self, entity, data):
        states = {}

        for name in data:
            states[name] = [
                self.get_state_condition(entity, *args) for args in data[name]
            ]

        return states

    def get_state_condition(self, entity, method_name, to_state, condition=True, buffer=False):
        return AnimationMachine.get_condition(
            lambda: getattr(self, method_name)(entity),
            to_state, condition=condition, buffer=buffer
        )

    def set_animations(self, entity, sprite_sheet, data_file):
        data = self.context.load_resource(data_file)

        scale = data.get("scale", 1)
        image = self.context.load_resource(sprite_sheet)
        if scale != 1:
            image = image.get_scaled(scale)

        graphics = AnimationGraphics(entity, image)
        entity.graphics = graphics

        graphics.animations = self.get_animations(data)
        entity.update_methods.append(graphics.update)
        graphics.reset_meter()

    def get_animations(self, data):
        animations = {}
        scale = data.get("scale", 1)
        cell_size = data.get("cell_size", (1, 1))

        default_data = data.get("data", {})
        default_duration = data.get("duration", 1)
        default_offset = data.get("footprint", (0, 0))

        for a in data["animations"]:
            name = a["name"]
            if type(a["steps"]) is str:
                other = animations[a["steps"]]
                animations[name] = other.get_mirror_animation(
                    name, a["mirror"]
                )

            else:
                footprint = a.get("footprint", default_offset)

                if "data" not in a:
                    a["data"] = {}
                a["data"].update(default_data)
                a["data"] = AnimationInterface.scale_box_data(
                    scale, footprint, a["data"]
                )

                if "duration" not in a:
                    a["duration"] = default_duration

                animations[name] = self.get_animation_object(
                    a, scale, cell_size, footprint
                )

        return animations

    @staticmethod
    def scale_values(scale, value):
        if type(value) not in (list, tuple):
            return value * scale

        else:
            return [AnimationInterface.scale_values(scale, v) for v in value]

    @staticmethod
    def scale_box_data(scale, footprint, box_data):
        sv = AnimationInterface.scale_values
        boxes = {}

        for name in box_data:
            b = box_data[name]
            box = {}

            if "size" in b:
                box["size"] = sv(scale, b["size"])

            if "position" in b:
                px, py = sv(scale, b["position"])
                fx, fy = footprint
                px -= fx * scale
                py -= fy * scale
                box["position"] = px, py

            if "radius" in b:
                box["radius"] = sv(scale, b["radius"])

            boxes[name] = box

        return boxes

    @staticmethod
    def get_animation_layer(data, scale, cell_size=(1, 1), footprint=(0, 0)):
        sv = AnimationInterface.scale_values

        # data = {
        #   "offset":   (int, int)      draw position               (0, 0) default
        #   "rect":     x, y, w, h      sprite sheet sub section    optional
        #   "position": col, row        sprite sheet grid position  optional
        #   "mirror":   x bool, y bool  flip transform              False, False default
        #   "rotate":   float           clockwise rotations         0.0 default
        # }

        if "rect" in data:
            x, y, w, h = sv(scale, data["rect"])
            size = w, h
            position = x, y
        else:
            cw, ch = sv(scale, cell_size)

            size = cw, ch
            row, col = data["position"]
            position = row * cw, col * ch

        ox, oy = data.get("offset", (0, 0))
        fx, fy = footprint
        offset = sv(scale, (ox - fx, oy - fy))

        mirror = data.get("mirror", (False, False))
        rotate = data.get("rotate", 0)

        return AnimationLayer(size, position, offset, mirror, rotate)

    def get_animation_step(self, step_data, scale, cell_size=(1, 1), footprint=(0, 0)):
        images = step_data["image"]
        if type(images) is dict:
            images = [images]

        layers = []
        for i in images:
            layers.append(
                self.get_animation_layer(i, scale, cell_size, footprint)
            )

        duration = step_data.get("duration", 1)
        data = step_data.get("data", {})
        data = AnimationInterface.scale_box_data(scale, footprint, data)

        return AnimationStep(duration, layers, data)

    def get_animation_object(self, animation_data, scale, cell_size=(1, 1), footprint=(0, 0)):
        steps = []

        for s in animation_data["steps"]:
            if "duration" not in s:
                s["duration"] = animation_data["duration"]

            steps.append(
                self.get_animation_step(s, scale, cell_size, footprint)
            )

        name = animation_data["name"]
        data = animation_data.get("data")

        return Animation(name, steps, data)


class AnimationGraphics(ImageSectionGraphics):
    def __init__(self, entity, image):
        super(AnimationGraphics, self).__init__(entity, image)

        self.animations = {}
        self.animation_meter = Meter(
            "{} animation meter".format(entity.name),
            0, 0, 1
        )

        self.get_state = None
        self.animation_cycles = 0

    def get_animation_state(self):
        if self.get_state:
            return self.get_state()

        else:
            return "walk"

    def update(self):
        meter = self.animation_meter
        if meter.is_full():
            self.animation_cycles += 1

        meter.next()
        self.update_image_layers()

    def update_image_layers(self):
        state = self.get_animation_state()
        self.layers = []

        if state in self.animations:
            animation = self.animations[state]
            step = animation.get_current_step(self.animation_meter.value)

            for layer in step.layers:
                rect = Rect(layer.size, layer.position)
                offset = layer.offset
                mirror = layer.mirror
                rotate = layer.rotate

                self.layers.append((rect, offset, mirror, rotate))

    def reset_meter(self):
        state = self.get_animation_state()
        self.animation_cycles = 0
        self.animation_meter.reset()

        if state in self.animations:
            animation = self.animations[state]
            self.animation_meter.maximum = animation.get_frame_count() - 1
            self.update_image_layers()
