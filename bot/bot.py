from code import interact
from bot.bot_ai_base import BotAIBase
from bot.strategies.Terran.strategy_terran_root import StrategyTerranRoot
from bot.strategies.zerg import StrategyZergRoot
from sc2.bot_ai import Race
from sc2.data import Result
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit

class CompetitiveBot(BotAIBase):
    NAME: str = "CompetitiveBot"
    """This bot's name"""

    RACE: Race = Race.Terran
    """This bot's Starcraft 2 race.
    Options are:
        Race.Terran
        Race.Zerg
        Race.Protoss
        Race.Random
    """


    def __init__(self) -> None:
        super().__init__()
        self.race = Race.Terran
        self.testrea = 5
    
    async def on_start(self):
        await super().on_start()

        await self.client.debug_show_map()
        #self.strategy = StrategyZergRoot(self)
        self.strategy = StrategyTerranRoot()
        self.strategy.post_init(self)
        
        self.strategy.start()

    async def on_step(self, iteration: int):
        await super().on_step(iteration)