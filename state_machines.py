class StateCondition:
    def __init__(self, method, to, condition=True, buffer=False):
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


class AnimationMachine(StateMachine):
    def __init__(self, entity, states):
        super(AnimationMachine, self).__init__(states)
        self.entity = entity
        self.buffer_check = self.animation_done

    def set_state(self, state):
        self.entity.set_animation_state(state)
        super(AnimationMachine, self).set_state(state)
        self.buffer_state = None

    def animation_done(self):
        return self.entity.graphics.animation_cycles > 0
