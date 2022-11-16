from bot.squads.squad_scout import SquadScout
from bot.strategies.strategy import Strategy
from sc2.unit import Unit

class StrategyTerranScout(Strategy):
    def __init__(self) -> None:
        super().__init__()
        self.squad_scout = None

    def add_unit(self, unit: Unit):
        self.squad_scout = SquadScout()
        self.add_squad(self.squad_scout)
        self.squad_scout.add_unit(unit)    

    def is_empty(self):
        return not self.squad_scout

    def debug_string(self) -> str:
        return "TerranScout"