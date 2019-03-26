from utils.cache_list import CacheList
from itertools import groupby


class CommandInput:
    def __init__(self, name, device_names, window, *steps):
        self.name = name
        self.steps = steps
        self.frames = CacheList(window)
        self.frame_window = window
        self.devices = device_names
        self.active = False

    def __repr__(self):
        return "{}: {}".format(self.__class__.__name__, self.name)

    def set_window(self, value):
        self.frame_window = value
        self.frames.set_size(value)

    def check(self):
        frames = self.frames
        length = len(frames)
        i = 0

        for step in self.steps:
            sub_slice = frames[i:length]
            j = step.check(sub_slice)
            step.last = j
            i += j

            if j == 0:
                return False

        return True

    def update(self, frame):
        if frame:
            self.frames.append(frame[-1])
        c = self.check()
        self.active = c

        if c:
            self.frames.clear()


class CommandStep:
    def __init__(self, name, window, *conditions):
        self.name = name
        self.frame_window = window
        self.conditions = conditions
        self.last = 0

    def __repr__(self):
        return "{}: {}".format(self.__class__.__name__, self.name)

    def get_matrix(self, frames):
        frame_matrix = []
        conditions = self.conditions

        for c in conditions:
            # row = [c.check(frame) for frame in frames]
            row = []
            for frame in frames:
                row.append(c.check(frame))

            frame_matrix.append(row)

        return frame_matrix

    def get_sub_matrix(self, frame_matrix, i):
        conditions = self.conditions
        fw = self.frame_window
        sub_matrix = []

        for con in conditions:
            row_i = conditions.index(con)
            row = frame_matrix[row_i][i:i + fw]
            sub_matrix.append(row)

        return sub_matrix

    def check(self, frames):
        frame_matrix = self.get_matrix(frames)
        fw = self.frame_window
        fl = len(frames)

        for i in range((fl - fw) + 1):
            sub_matrix = self.get_sub_matrix(frame_matrix, i)
            truth = all([any(row) for row in sub_matrix])

            if truth:
                return i + 1

        return 0


class CommandCondition:
    def __init__(self, *args):
        self.check = self.get_condition(*args)

    @staticmethod
    def split_by(seq, key):
        groups = groupby(seq, lambda i: i == key)
        return [i for i in [list(g[1]) for g in groups] if i[0] != key]

    def get_condition(self, *args):
        if "or" in args:
            check_funcs = self.split_by(args, "or")
            return lambda f: any([
                self.get_condition(*cf)(f) for cf in check_funcs
            ])

        elif "and" in args:
            check_funcs = self.split_by(args, "and")
            return lambda f: all([
                self.get_condition(*cf)(f) for cf in check_funcs
            ])

        else:
            return self.get_check_func(*args)

    @staticmethod
    def get_check_func(*args):
        if type(args[0]) == CommandCondition:
            return args[0].check

        i, comparison, target = args
        return {
            "==": lambda f: f[i] == target,
            "!=": lambda f: f[i] != target,
            ">": lambda f: f[i] > target,
            ">=": lambda f: f[i] >= target,
            "<": lambda f: f[i] < target,
            "<=": lambda f: f[i] <= target
        }[comparison]
