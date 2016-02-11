class StateMachine(object):

    def __init__(self, initial_state):
        self.current_state = initial_state
        self.current_state.run()

    def run(self, action, **kwargs):
        self.current_state = self.current_state.transition(action, **kwargs)
        self.current_state.run()


class StateMachineException(Exception):
    pass


class InvalidStateTransition(StateMachineException):
    pass


class State(object):

    def __init__(self, state):
        self.state = state
        self.transitions = {}

    def transition(self, action, **kwargs):
        try:
            new_state = self.transitions[action]
        except KeyError:
            raise InvalidStateTransition(
                '%s is not a valid action. Valid actions are: %s' % (
                    action, self.transitions.keys()))

        if hasattr(self, action):
            return getattr(self, action)(**kwargs)

        return new_state

    def run(self):
        pass
