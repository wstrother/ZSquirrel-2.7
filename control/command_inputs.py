from zsquirrel.utils.cache_list import CacheList
from itertools import groupby

"""
The command_inputs.py module is intended to provide hashable keys and data that can be used
to identify certain patterns of input over a certain span of frames across one or more input
devices.
"""


class CommandInput:
    """

    """
    def __init__(self, name, device_names, window, *steps):
        """
        :param name: (str) hashable key to identify a pattern of input
        :param device_names: (iterable) hashable keys for each relevant input device
        :param window: (int) the maximum span of frames that an input pattern should be identified
            in to register as being completed
        :param steps: (iterable) CommandStep objects that specify the pattern of input
        """
        self.name = name
        self.steps = steps
        self.frames = CacheList(window)
        self.frame_window = window
        self.devices = device_names
        self.active = False

    def __repr__(self):
        return "{}: {}".format(self.__class__.__name__, self.name)

    def check(self):
        """
        This method iterates over each CommandStep object in the 'steps' attribute and calls
        their check() method with a slice of the current frame cache in the 'frames' attribute.
        Each time a CommandStep is detected within the current slice, it returns the earliest
        frame index where that step counts as detected, and that index is used to form the beginning
        of the next sub slice.

        If all the steps are detected then the check() method returns True, but if any of the
        steps is not detected in the given frames slice then check() returns False

        :return: (bool) whether or not all the CommandStep objects are detected
            within the current frame cache
        """
        frames = self.frames
        length = len(frames)
        i = 0

        for step in self.steps:
            sub_slice = frames[i:length]
            j = step.check(sub_slice)
            i += j

            if j is False:
                return False

        return True

    def update(self, frame):
        """
        The update method calls the check() method after updating the 'frames' attribute with
        data passed by a Controller object. The 'active' method is set to the bool value returned
        by the check() method and if the value is True then the frame cache is cleared.

        :param frame: (list) input data passed from the Controller.update() method
        """
        if frame:
            self.frames.append(frame[-1])
        c = self.check()
        self.active = c

        if c:
            self.frames.clear()


class CommandStep:
    """
    The CommandStep class defines an object which represents a given 'step' within a CommandInput pattern.
    Each step has a given frame window that each of it's conditions must be satisfied within in order to
    count as being detected in the frames passed by CommandInput's check() method
    """
    def __init__(self, name, window, *conditions):
        """
        :param name: (str) hashable name to identify CommandStep object in data
        :param window: (int) the maximum window of frames that all of the given CommandCondition
            checks must be satisfied within
        :param conditions: CommandCondition objects
        """
        self.name = name
        self.frame_window = window
        self.conditions = conditions

    def __repr__(self):
        return "{}: {}".format(self.__class__.__name__, self.name)

    def get_matrix(self, frames):
        """
        This method takes a window of frames and uses their input data to generate a new
        2D array (list of lists) with bools that represent which frames' input data satisfies
        which CommandCondition in the 'conditions' attribute list.

        :param frames: (list) window of frames to check input data against command conditions
        :return: (list) 2D array of bool values that correspond to whether each command condition
            returns True when it's check() method is called with a given frame of input data
        """
        frame_matrix = []
        conditions = self.conditions

        for c in conditions:
            row = []
            for frame in frames:
                row.append(c.check(frame))

            frame_matrix.append(row)

        return frame_matrix

    def get_sub_matrix(self, frame_matrix, i):
        """
        This method returns a sub slice of the entire frame_matrix as returned by get_matrix()
        starting at a given offset which corresponds to the current frame index being checked
        in the CommandStep.check() method

        :param frame_matrix: (list) 2D array of bool values as returned by get_matrix()
        :param i: (int) the current frame index
        :return: (list) sub slice of the passed frame_matrix
        """
        conditions = self.conditions
        fw = self.frame_window
        sub_matrix = []

        for con in conditions:
            row_i = conditions.index(con)
            row = frame_matrix[row_i][i:i + fw]
            sub_matrix.append(row)

        return sub_matrix

    def check(self, frames):
        """
        This method returns an integer representing the earliest frame on which all of the
        CommandCondition objects in the 'conditions' attribute return True from their check()
        method. If all the conditions are not met in the given frames then False is returned

        :param frames: (list) window of frames to check input data against command conditions
        :return: (int) frame index or (bool) False
        """
        frame_matrix = self.get_matrix(frames)
        fw = self.frame_window
        fl = len(frames)

        for i in range((fl - fw) + 1):
            sub_matrix = self.get_sub_matrix(frame_matrix, i)
            truth = all([any(row) for row in sub_matrix])

            if truth:
                return i + 1

        return False


class CommandCondition:
    """
    The CommandCondition class defines objects that yield a 'check' method to be called
    in conjunction with the CommandStep class in order to identify a specific set of conditions
    that are checked for on a given frame of input data.

    The argument signature that CommandCondition objects are initialized with is complex
    and the individual arguments combine recursively to form expressions equivalent to regular
    Python syntax. The various forms each argument can take are:

        (str) 'or' / 'and' corresponding to the logical operators in Python
        (str) '==', '!=', '>', '>=', '<', '<=' corresponding to the comparative operators in Python
        (int) corresponding to the index of an InputDevice object as specified in the
            initialization of a given CommandInput object
        (int or float) corresponding to a targeted value in an comparison expression
        (CommandCondition object) used to substitute a given set of arguments by yielding
            its own 'check' attribute function in the get_comparison() method
    """
    def __init__(self, *args):
        """
        :param args: args to be passed to get_check_func()
        """
        self.check = self.get_check_func(*args)

    @staticmethod
    def split_by(seq, key):
        """
        This static method returns a list that recursively groups the argument sequence
        passed to get_check_funcs() into separate lists, as broken up by the corresponding
        'key' parameter

        :param seq: (iterable) args parameters as passed to get_check_func()
        :param key: (str) either 'or' or 'and'
        :return: (list) [(args for get_check_func), ...] to be used recursively
        """
        groups = groupby(seq, lambda i: i == key)
        return [i for i in [list(g[1]) for g in groups] if i[0] != key]

    # get_check_func() args:
    # (get_comparison() args)
    #       or
    # (str) 'or'
    #       or
    # (str) 'and'
    def get_check_func(self, *args):
        """
        This method returns an anonymous function that takes a given frame of input data
        and checks it against a series of comparison expressions as defined by the
        args parameters that are passed to the CommandCondition object on initialization.

        The arguments passed can be grouped recursively into one or more comparison
        expressions using the same signature as the CommandCondition.get_comparison() method.
        Those expressions can also be separated by the string 'and' / 'or' to form more
        complex expressions. The 'and' / 'or' strings should evaluate to the equivalent
        expression in regular Python syntax

        :param args: (get_comparison() signature)
                            or
                    (str) 'or'
                            or
                    (str) 'and'
        :return: (function) function that returns a bool representing whether a given frame
            of input data satisfies the expression defined by the sequence of 'args' parameters
        """
        if "or" in args:
            check_funcs = self.split_by(args, "or")
            return lambda f: any([
                self.get_check_func(*cf)(f) for cf in check_funcs
            ])

        elif "and" in args:
            check_funcs = self.split_by(args, "and")
            return lambda f: all([
                self.get_check_func(*cf)(f) for cf in check_funcs
            ])

        else:
            return self.get_comparison(*args)

    # get_comparison() args:
    # CommandCondition object
    #       or
    # (int) 'i', (str) 'comparison', (int or float) 'target'
    @staticmethod
    def get_comparison(*args):
        """
        This static method simply interprets a set of arguments and returns an anonymous function
        that takes a single input value from a single frame and returns a bool based on some comparison

        The parameters passed to this method can take the form of either a single CommandCondition object
        (in which case it's 'check' attribute will be returned)
             or
        3 specific parameters consisting of an int 'i', a str 'comparison' and a float or int 'target'
            the 'i' parameter defines the index of the particular device to be checked within a given
                frame of input data. This index is should correspond to the index of the of
                InputDevice subclass object's name as specified in the relevant CommandInput object,
                NOT the index of the Controller object's 'devices' list.
            the 'comparison' parameter defines the comparison operation that should be used, and she
                be the string literal of that comparison operator in Python.
            the 'target' parameter defines either an int or float that should be checked against as
                the final part of the comparison expression

        :param args: (CommandCondition object)
                        or
                    (str, str, int or float) hashable args for simple comparison expression
        :return: (function) function that returns a bool based on a comparison expression with
                a specific input value for an individual frame
        """
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
