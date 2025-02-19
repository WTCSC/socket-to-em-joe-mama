import random

class RussianRouletteGame:
    def __init__(self, players):
        self.players = players
        self.current_turn = 0
        self.bullet_chamber = [False] * 5 + [True]
        random.shuffle(self.bullet_chamber)

    def fire(self):
        """Simulates firing the gun."""
        fired = self.bullet_chamber.pop(0)
        if fired:
            eliminated = self.players.pop(self.current_turn)
            return eliminated
        else:
            self.current_turn = (self.current_turn + 1) % len(self.players)
        return None
