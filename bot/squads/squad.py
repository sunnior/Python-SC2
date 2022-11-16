from sc2.bot_ai import BotAI
from sc2.unit import Unit


class Squad():
    def __init__(self) -> None:
        self.bot: BotAI = None
        self.units: list[int] = []
        
    def on_added(self, bot: BotAI):
        self.bot = bot
    
    def add_unit(self, unit: Unit):
        self.units.append(unit.tag)

    def remove_unit(self, unit: Unit):
        self.units.remove(unit.tag)
    
    def step(self):
        pass

    def on_building_construction_complete(self, unit: Unit):
        pass

    def on_my_unit_destroyed(self, unit: Unit):
        assert(False)

    def on_unit_destroyed(self, unit: Unit):
        if unit.tag in self.units:
            self.on_my_unit_destroyed(unit)
            self.units.remove(unit.tag)

    def debug_string(self) -> str:
        return "Unkown"
