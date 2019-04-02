class StateCondition:
    def __init__(self, method, to, condition=True, buffer=False):
        self.name = method.__name__
        self.to_state = to
        self._method = method
        self.test_condition = condition
        self.buffer = buffer

    def test(self):
        return self.test_condition is bool(self._method())


class StateMachine:
    def __init__(self, states):
        self.states = states
        self.state = list(states.keys())[0]

        self.buffer_state = None
        self.buffer_check = None

    @staticmethod
    def get_condition(method, to, condition=True, buffer=False, name=None):
        c = StateCondition(method, to, condition=condition, buffer=buffer)

        if name:
            c.name = name

        return c

    def get_state(self):
        return self.state

    def set_state(self, state):
        self.state = state

    @property
    def conditions(self):
        if self.state in self.states:
            return self.states[self.state]

    def update(self):
        if self.conditions:
            if self.buffer_state and self.buffer_check:
                if self.buffer_check():
                    self.set_state(self.buffer_state)
                    return

            for c in self.conditions:
                if c.test():
                    if not c.buffer:
                        self.set_state(c.to_state)

                    else:
                        self.buffer_state = c.to_state
