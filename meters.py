class Meter:
    """
    Meter objects have a minimum, value, and maximum attribute (int or float)
    The normalize method is called when one of these attributes is assigned to
    ensuring that value stays in the proper range.
    Use of property objects as attributes allows for some automatic edge case
    handling. Be aware that by design Meter objects will try to make assignments
    work rather than throw errors. E.G. passing a minimum lower than maximum
    to __init__ raises ValueError, but the 'maximum' / 'minimum' setters will
    automatically normalize assignments to an acceptable range.
    Meter is designed to make composed attributes and to allow for flexible
    dynamic use so if you want to ensure edge case errors, that logic will
    need to be implemented by the relevant Entity in the game engine.
    """
    # Meter(name, value) ->                     minimum = 0, value = value, maximum = value
    # Meter(name, value, maximum) ->            minimum = 0, value = value, maximum = maximum
    # Meter(name, minimum, value, maximum) ->   minimum = 0, value = value, maximum = maximum
    def __init__(self, name, *args):
        value = args[0]
        maximum = args[0]
        minimum = 0
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

        if maximum < minimum:     # minimum should always be leq than maximum
            raise ValueError("bad maximum / minimum values passed to meter object")
        self.normalize()

    def __repr__(self):
        sf = 4
        n, v, m, r = (self.name,
                      round(self.value, sf),
                      round(self._maximum, sf),
                      round(self.get_ratio(), sf))

        return "{}: {}/{} r: {}".format(n, v, m, r)

    # getters and setters
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self.normalize()

    @property
    def minimum(self):
        return self._minimum

    @minimum.setter
    def minimum(self, value):
        if value > self.maximum:
            value = self.maximum

        self._minimum = value
        self.normalize()

    @property
    def maximum(self):
        return self._maximum

    @maximum.setter
    def maximum(self, value):
        if value < self.minimum:
            value = self.minimum

        self._maximum = value
        self.normalize()

    # methods
    def normalize(self):        # sets value to be inside min / max range
        in_bounds = True

        if self._value > self.maximum:
            self._value = self.maximum
            in_bounds = False

        if self._value < self.minimum:
            self._value = self.minimum
            in_bounds = False

        # this return value is mainly for debugging
        # and unit testing
        return in_bounds

    def refill(self):
        self.value = self.maximum

        return self.value

    def reset(self):
        self.value = self.minimum

        return self.value

    def get_ratio(self):
        span = self.get_span()
        value_span = self.value - self.minimum

        if span != 0:
            return value_span / span
        else:
            # calling "get_ratio" on a Meter object with a span of 0
            # will raise an ArithmeticError. There's no real way to
            # handle this edge case dynamically without creating
            # very weird, unintuitive behavior
            raise ArithmeticError("meter object has span of 0")

    def get_span(self):
        return self.maximum - self.minimum

    def is_full(self):
        return self.value == self.maximum

    def is_empty(self):
        return self.value == self.minimum

    def next(self):
        if self.is_full():
            self.reset()
        else:
            self.value += 1
            if self.value > self.maximum:
                dv = self.value - self.maximum
                self.value = dv

        return self.value

    def prev(self):
        if self.is_empty():
            self.refill()
        else:
            self.value -= 1
            if self.value < self.minimum:
                dv = self.value - self.minimum
                self.value = self.maximum - dv

        return self.value

    def shift(self, val):
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
    Timer objects have a set duration stored as frames.
    An optional on_tick() method is called on every frame the timer is
    ticked, and the on_switch_off() method is called on the frame that the
    Timer's value reaches 0.
    The temp flag determines if the timer will be removed by the Clock
    object that calls it's tick() method.
    """
    def __init__(self, name, duration, temp=True,
                 on_tick=None, on_switch_off=None):
        if duration <= 0:
            raise ValueError("bad duration", 0)
        super(Timer, self).__init__(name, duration)

        self.is_off = self.is_empty
        self.reset = self.refill
        self.temp = temp

        if on_tick:
            self.on_tick = on_tick
        if on_switch_off:
            self.on_switch_off = on_switch_off

    def __repr__(self):
        sf = 4
        n, v, m = (self.name,
                   round(self.value, sf),
                   round(self._maximum, sf))

        return "Timer: {} {}/{}".format(n, v, m)

    def is_on(self):
        return not self.is_off()

    def get_ratio(self):
        r = super(Timer, self).get_ratio()

        return 1 - r    # r should increase from 0 to 1 as the timer ticks

    def tick(self):
        before = self.is_on()

        self.value -= 1
        self.on_tick()

        after = self.is_off()
        switch_off = before and after

        if switch_off:
            self.on_switch_off()

        return switch_off

    def on_tick(self):
        pass

    def on_switch_off(self):
        pass


class Clock:
    """
    A Clock object simply contains a list of timers and calls
    tick() on each once per frame (assuming it's tick() method
    is called once per frame).
    A 'queue' and 'to_remove' list are used to create a one frame
    buffer between add_timers() and remove_timer() calls. This helps
    avoid some bugs that would break the for loop in tick() if another
    part of the stack calls those methods before the tick() method has
    fully executed.
    Timers with the temp flag set are removed when their value reaches 0
    but are reset on the frame their value reaches 0 if the flag is not
    set.
    """
    def __init__(self, name, timers=None):
        self.name = name
        self.timers = []
        self.queue = []
        self.to_remove = []

        if timers:
            self.add_timers(*timers)

    def __repr__(self):
        return self.name

    def add_timers(self, *timers):
        for timer in timers:
            self.queue.append(timer)

    def remove_timer(self, name):
        to_remove = []

        for t in self.timers:
            if t not in self.to_remove:     # remove_timer() checks the queue list
                if t.name == name:          # for matches as well as the active
                    to_remove.append(t)     # timers list

        for t in self.queue:
            if t not in self.to_remove:
                if t.name == name:
                    to_remove.append(t)

        self.to_remove += to_remove

    def tick(self):
        for t in self.queue:                # add queue timers to active timers list
            if t not in self.to_remove:     # unless that timer is set to be removed
                self.timers.append(t)

        self.queue = []
        tr = self.to_remove
        timers = [t for t in self.timers if t not in tr]

        for t in timers:
            t.tick()

            if t.is_off():              # timers without the temp flag set to True
                if not t.temp:          # will be reset when their value reaches 0
                    t.reset()
                else:
                    self.to_remove.append(t)

        self.timers = [t for t in timers if t not in tr]
        self.to_remove = []
