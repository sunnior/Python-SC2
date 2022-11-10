from typing import Optional
from bot.bot_ai_base import BotAIBase
from bot.squads.squad_mining import SquadMining
from bot.strategies.strategy import Strategy
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit

class StrategyTerranArmy(Strategy):
    def __init__(self) -> None:
        super().__init__()

    def post_init(self, bot: BotAIBase):
        super().post_init(bot)

        #self.act_order_tank = ActOrderTerranUnit(UnitTypeId.SIEGETANK, 999)

        path = self.bot.map_data.pathfind(self.bot.start_location, self.bot.enemy_start_locations[0])
        self.rally_point_small = path[min(len(path) - 1, 40)]
        path = self.bot.map_data.pathfind(self.bot.start_location, self.bot.enemy_start_locations[0], large=True)
        self.rally_point_large = path[min(len(path), 36)]

    def debug_string(self) -> str:
        return "TerranArmy"

    async def step(self):
        pass

    def on_build_complete(self, unit: Unit):
        if unit.type_id == UnitTypeId.BARRACKS:
            unit(AbilityId.RALLY_BUILDING, self.rally_point_small)
        elif unit.type_id == UnitTypeId.FACTORY:
            unit(AbilityId.RALLY_BUILDING, self.rally_point_large)

