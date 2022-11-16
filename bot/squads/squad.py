from sc2.bot_ai import BotAI
from sc2.unit import Unit


class Squad():
    def __init__(self) -> None:
        self.bot: BotAI = None
        
    def on_added(self, bot: BotAI):
        self.bot = bot
    
    def step(self):
        pass

    def on_building_construction_complete(self, unit: Unit):
        pass

    def debug_string(self) -> str:
        return "Unkown"
