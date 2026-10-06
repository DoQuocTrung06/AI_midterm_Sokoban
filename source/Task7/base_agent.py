class BaseAgent:
    def __init__(self, player_id):
        self.player_id = player_id

    def get_action(self, state, time_limit):
        raise NotImplementedError("Get action must be implemented in the subclass.")