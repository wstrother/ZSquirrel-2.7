# The meters.py module provides a few classes that operate as numeric value handlers.
#
# The general Meter class defines a minimum, maximum, and current value for some object
#   and some utility methods, such as returning the value as a ratio, or modularly
#   incrementing/decrementing it's value
#
# The Timer and Clock classes define a way to hold a frame timer value which decrements
#   each frame and potentially calls methods each frame or once they're finished
#   decrementing. They are defined as temporary by default and automatically removed from
#   the Clock object's timer list unless the 'temp' flag is set to False


class Meter:
    """
    The Meter class defines a type of object that essentially acts as a 'container'
    for numeric values. The object defines some minimum, maximum, and current value
    as attributes and extends object properties to ensure that the 'value' attribute
    is always within the span from 'minimum' to 'maximum'.
    Additional methods can return the value as a normalized ratio within the min-max
    span, or provide test methods that return bools for whether the Meter is 'full'
    or 'empty.'
    Additionally, the next(), prev() and shift() methods provide modular shifting
    functions that treat the Meter as having a discrete set of 'states' equal to
    it's span.
    """
    def __init__(self, name, *args):
        """
        Accepts a name str and one of three optional expressions to determine the
        Meter object's minimum, value, and maximum attributes.
        Meter(name, value) ->                     minimum = 0, value = value, maximum = value
        Meter(name, value, maximum) ->            minimum = 0, value = value, maximum = maximum
        Meter(name, minimum, value, maximum) ->   minimum = minimum, value = value, maximum = maximum
        If maximum is less than minimum and ValueError is raised.
        If maximum and minimum are not integer values a ValueError is raised.
        :param name: str
        :param args: (int or float, ...)
        """
        value = args[0]
        maximum = args[0]
        minimum = 0

        for arg in args:
            if type(arg) not in (int, float):
                raise ValueError("bad argument passed to Meter(): '{}' must be int or float".format(arg))

        if len(args) == 2:
            maximum = args[1]

        if len(args) == 3:
            minimum = args[0]
            value = args[1]
            maximum = args[2]

        self.name = name
        self._value = value
        self._maximum = maximum
        self._minimum = minimum

        if maximum < minimum:
            raise ValueError(
                "bad maximum / minimum values passed to Meter: {}".format(name)
            )

        if (int(maximum) != maximum) or (int(minimum) != minimum):
            raise ValueError(
                "bad maximum or minimum values passed to Meter: {} (must be integers)".format(name)
            )

        self.value = value

    def __repr__(self):
        """
        Returns description of Meter object including value, maximum, and
        fullness ratio up to 4 significant figures
        :return: str
        """
        sf = 4

        return "{} {}: {}/{} r: {}".format(
            self.__class__.__name__,
            self.name,
            round(self.value, sf),
            round(self._maximum, sf),
            round(self.get_ratio(), sf)
        )

    # getters and setters

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if type(value) not in (int, float):
            raise ValueError(
                "bad value passed to {} (must be int or float".format(self)
            )
        self._value = value
        self.fix_value()

    @property
    def minimum(self):
        return self._minimum

    @minimum.setter
    def minimum(self, value):
        if value > self.maximum:
            value = self.maximum

        self._minimum = value
        self.fix_value()

    @property
    def maximum(self):
        return self._maximum

    @maximum.setter
    def maximum(self, value):
        self._maximum = value
        self.fix_value()

    # methods

    def fix_value(self):
        """
        Fixes the value attribute so that it is always between (inclusive)
        the Meter object's maximum and minimum values.
        Also returns a bool of false or true based on whether a correction
        was made. Mainly used for diagnostic / testing purposes.
        :return: bool
        """
        in_bounds = True

        if self._value > self._maximum:
            self._value = self._maximum
            in_bounds = False

        if self._value < self._minimum:
            self._value = self._minimum
            in_bounds = False

        return in_bounds

    def refill(self):
        """
        Sets the Meter object's value to it's maximum.
        Also returns the maximum value.
        :return: int or float
        """
        self._value = self._maximum

        return self._value

    def reset(self):
        """
        Sets the Meter object's value to it's minimum.
        Also returns the minimum value.
        :return: int or float
        """
        self._value = self.minimum

        return self._value

    def get_ratio(self):
        """
        Returns the fullness of the Meter's value relative to the
        total span as a float between 0 and 1.
        If the Meter has a span of 0 this method raises an ArithmeticError
        :return: float
        """
        span = self.get_span()
        value_span = self._value - self._minimum

        if span != 0:
            return value_span / span

        else:
            raise ArithmeticError(
                "meter object {} has span of 0".format(self.name)
            )

    def get_span(self):
        """
        Returns the difference between Meter object's maximum and minimum
        :return: int or float
        """
        return self._maximum - self._minimum

    def is_full(self):
        """
        Tests whether Meter object's value is equal to it's maximum.
        :return: bool
        """
        return self._value == self._maximum

    def is_empty(self):
        """
        Tests whether the Meter object's value is equal to it's minimum.
        :return: bool
        """
        return self._value == self._minimum

    def next(self):
        """
        Adds 1 to Meter object's value modularly.
        This method floors and casts the current Meter object's value to int.
        :return: int
        """
        v = int(self.value // 1)
        v += 1

        if v > self._maximum:
            v -= self.get_span() + 1

        self.value = v

        return self._value

    def prev(self):
        """
        Same as Meter.next() method but with subtraction instead of addition
        This method floors and casts the current Meter object's value to int.
        :return: int or float
        """
        v = int(self._value // 1)
        v -= 1

        if v < self._minimum:
            v += self.get_span() + 1

        self.value = v

        return self._value

    def shift(self, val):
        """
        Shifts the value of the Meter object modularly based on the 'val' argument.
        Positive integers will cause the next() method to be called, and negative
        integers will cause the prev() method to be called. The 'val' argument
        passed is divided modularly by the Meter's span so only the minimum amount
        of method calls needed will be made.
        :param val: int, number of calls to next() or prev()
        :return: int or float
        """
        dv = abs(val) % (self.get_span() + 1)

        if val > 0:
            for x in range(dv):
                self.next()

        if val < 0:
            for x in range(dv):
                self.prev()

        return self.value


class Timer(Meter):
    """
    The Timer object is a type of Meter than effectively operates as a frame timer.
    Typically, when used with a Clock object by calling the Clock.tick() method
    each frame, it can call an optional 'on_tick' method each frame or the 'on_done'
    method when the Timer value is set to 0. The Clock will also remove any timers
    that have their 'temp' flag set to True, or reset them otherwise.
    """
    def __init__(self, name, duration, temp=True, on_tick=None, on_done=None):
        """
        Timer object's take an integer duration greater than 0, (otherwise a
        ValueError will be raised), which counts down each time the tick()
        method is called.
        An optional 'temp' flag is used by any Clock object to determine whether
        a Timer should be removed when it's value reaches 0.
        Two optional methods can be passed to the Timer object:
            'on_tick': Called each time the 'tick' method is called
            'on_done': Called whenever the 'tick' method decrements the value to 0
        :param name: str
        :param duration: int
        :param temp: bool
        :param on_tick: None or method
        :param on_done: None or method
        """
        if (type(duration) is not int) or (duration <= 0):
            raise ValueError(
                "Bad duration ({}) passed to Timer: {}".format(duration, name)
            )

        super(Timer, self).__init__(name, duration)

        self.reset = self.refill
        self.temp = bool(temp)

        self.on_tick = None
        self.on_done = None

        if on_tick:
            self.on_tick = on_tick

        if on_done:
            self.on_done = on_done

    def is_off(self):
        """
        Returns True if the Timer's value is 0
        :return: bool
        """
        return self.is_empty()

    def is_on(self):
        """
        Returns True whenever the Timer's value is greater than 0
        :return: bool
        """
        return not self.is_off()

    def get_ratio(self):
        """
        Returns the normalized ratio from the parent class Meter's
        'get_ratio()' function subtracted from 1.
        I.E.: As the Timer's value decrements the ratio will increase
        from 0 to 1.
        :return: int
        """
        r = super(Timer, self).get_ratio()

        return 1 - r

    def tick(self):
        """
        Decrements the Timer's value by 1 and calls the 'on_tick' method
        if it is set. The value decrements from 1 to 0 the 'on_done' method
        is then also called.
        This method returns True as long as the Timer value is still greater
        than 0.
        If timer is not on (the 'value' attr is set to 0) when tick() is called
        nothing happens and None is returned
        :return: bool or None
        """
        before = self.is_on()
        if before:
            self.prev()

            if self.on_tick:
                self.on_tick()

            after = self.is_off()
            done = before and after

            if done and self.on_done:
                self.on_done()

            return done

        else:
            return None


class Clock:
    """
    The Clock object simply manages a list of Timer objects. It's 'tick' method
    should be called once per frame, usually by an Entity object, which will
    call each Timer's 'tick()' method as well and remove any Timers set to be
    temporary.
    """
    def __init__(self, name, timers=None):
        """
        Takes an optional list of Timer objects to be updated by the tick()
        method.
        :param name: str
        :param timers: list [Timer, ...]
        """
        self.name = name
        self.timers = []
        self.to_remove = []
        self.to_add = []

        if timers:
            self.add_timers(*timers)

    def __repr__(self):
        return "{} {}".format(
            self.__class__.__name__,
            self.name
        )

    def add_timers(self, *timers):
        """
        Add a list of Timer objects to the to_add list
        Timers in the to_add list are only added to the main timers list
        when tick() is called
        :param timers: list [Timer, ...]
        :return:
        """
        self.to_add += timers

    def remove_timer(self, timer):
        """
        Adds a timer to the to_remove list
        Timers in the to_remove list are only removed from the main timers
        list when tick() is called
        :param timer: Timer
        """
        remove = None

        timers = self.timers + self.to_add

        for t in timers:
            if t is timer:
                remove = t

        if remove:
            self.to_remove.append(remove)

    def tick(self):
        """
        Calls the 'tick' method on each Timer in the timers list.
        If the Timer's 'is_off' method returns True, it will either be removed
        if it's 'temp' flag is set to True, or else its 'reset' method will
        be called
        Timers in the to_add list are added to the main Clock.timers list before
        each timer's tick() method is called individually
        Timers in the 'to_remove' list are removed from the main Clock.timers
        list after each timer's tick() method is called individually, but any
        timer that is already in the 'to_remove' list will be skipped and its
        tick() method will not be called
        If a timer is added to the to_remove list by another method while
        tick() is still executing, it's tick() method will not be called
        """
        self.timers += self.to_add
        self.to_add = []

        for t in self.timers:
            if t not in self.to_remove:
                t.tick()

                if t.is_off():
                    if t.temp:
                        self.remove_timer(t)
                    else:
                        t.reset()

        self.timers = [
            t for t in self.timers if t not in self.to_remove
        ]
        self.to_remove = []
