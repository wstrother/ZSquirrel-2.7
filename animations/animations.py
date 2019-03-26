from copy import copy
import zsquirrel.constants as con
from zsquirrel.utils.state_machines import StateMachine


class Animation:
    def __init__(self, name, steps, data=None):
        self.name = name
        self.steps = steps

        if not data:
            data = {}

        self.data = data

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

    def get_reverse_animation(self, name):
        new_steps = [
            s for s in self.steps
        ]
        new_steps.reverse()
        new_data = self.data.copy()

        return Animation(name, new_steps, new_data)

    @staticmethod
    def get_mirror_data(data, mirror):
        new_data = {}
        x_flip, y_flip = mirror

        for key in data:
            new_data[key] = copy(data[key])
            item = new_data[key]

            if con.SIZE in item:
                w, h = item[con.SIZE]
            else:
                w, h = item[con.RADIUS], item[con.RADIUS]

            if con.POSITION in item:
                x, y = item[con.POSITION]
                if x_flip:
                    x *= -1
                    x -= w
                if y_flip:
                    y *= -1
                    y -= h

                item[con.POSITION] = x, y

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


class AnimationMachine(StateMachine):
    def __init__(self, entity, states):
        super(AnimationMachine, self).__init__(states)
        self.entity = entity
        self.buffer_check = self.animation_done
        self.sounds = {}

    def set_state(self, state):
        old = self.get_state()
        self.handle_sound_off(old)

        super(AnimationMachine, self).set_state(state)

        self.entity.handle_event({
            "name": "change_state",
            "state": state,
            "last_state": old
        })
        self.entity.graphics.reset_meter()
        self.buffer_state = None

    def animation_done(self):
        return self.entity.graphics.animation_cycles > 0

    def update(self):
        super(AnimationMachine, self).update()
        self.handle_sound(self.get_state())

    def get_state_sounds(self, state):
        if state in self.sounds:
            return self.sounds[state]

        else:
            return []

    def handle_sound(self, state):
        sounds = self.get_state_sounds(state)
        frame = self.entity.graphics.animation_meter.value
        cycles = self.entity.graphics.animation_cycles

        for item in sounds:
            file = item["file"]
            play_frame = frame == item.get("offset", 0)
            loop = item.get("loop", False)
            if loop:
                play_sound = play_frame
            else:
                play_sound = play_frame and cycles == 0

            if play_sound:
                file.play()

    def handle_sound_off(self, state):
        sounds = self.get_state_sounds(state)

        for item in sounds:
            file = item["file"]
            cancel = item.get("cancel", True)
            if cancel:
                file.stop()
