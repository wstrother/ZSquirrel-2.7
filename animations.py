from copy import copy


class Animation:
    def __init__(self, name, steps, data=None):
        self.name = name
        self.steps = steps

        if not data:
            data = {}

        self.data = data

    # def add_step(self, duration, layers, data=None):
    #     self.steps.append(
    #         AnimationStep(duration, layers, data)
    #     )

    def get_current_step(self, frame_num):
        for s in self.steps:
            d = s.duration
            frame_num -= d
            if frame_num <= 0:
                return s

    def get_step_index(self, frame_num):
        i = 0
        for d in [s.duration for s in self.steps]:
            frame_num -= d

            if frame_num < 0:
                return i

            i += 1

    def get_frame_count(self):
        i = 0
        for s in self.steps:
            d = s.duration
            i += d

        return i

    def get_mirror_animation(self, name, mirror):
        new_steps = [
            s.get_mirror_step(mirror) for s in self.steps
        ]

        new_data = self.get_mirror_data(self.data, mirror)

        return Animation(name, new_steps, new_data)

    @staticmethod
    def get_mirror_data(data, mirror):
        new_data = {}
        x_flip, y_flip = mirror

        for key in data:
            new_data[key] = copy(data[key])
            item = new_data[key]

            if "size" in item:
                w, h = item["size"]
            else:
                w, h = item["radius"], item["radius"]

            if "position" in item:
                x, y = item["position"]
                if x_flip:
                    x *= -1
                    x -= w
                if y_flip:
                    y *= -1
                    y -= h

                item["position"] = x, y

        return new_data


class AnimationStep:
    def __init__(self, duration, layers, data=None):
        self.duration = duration
        self.layers = layers

        if not data:
            data = {}

        self.data = data

    def get_mirror_step(self, mirror):
        layers = [l.get_mirror_layer(mirror) for l in self.layers]
        data = Animation.get_mirror_data(self.data, mirror)

        return AnimationStep(self.duration, layers, data)


class AnimationLayer:
    def __init__(self, size, position, offset, mirror=(False, False), rotate=0):
        self.size = size
        self.position = position
        self.offset = offset
        self.mirror = mirror
        self.rotate = rotate

    def get_mirror_layer(self, mirror):
        x_flip, y_flip = mirror
        ox, oy = self.offset
        w, h = self.size
        new_mx, new_my = self.mirror

        if x_flip:
            ox *= -1
            ox -= w
            new_mx = not new_mx
        if y_flip:
            oy *= -1
            oy -= h
            new_my = not new_my

        return AnimationLayer(
            self.size, self.position,
            (ox, oy), (new_mx, new_my),
            self.rotate
        )
