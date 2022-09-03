from typing import Optional
from bot.acts.act_base import ActBase
from bot.acts.act_check_unit import ActCheckSupplyUsed
from bot.acts.act_order import ActOrderBuild
from bot.acts.act_flow_control import ActLoop, ActSequence, ActAnd
from bot.acts.interface_build_helper import InterfaceBuildHelper
from bot.bot_ai_base import BotAIBase
from bot.strategies.strategy import Strategy
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2

class ActCheckTerranSupplyAuto(ActBase):
    def __init__(self):
        super().__init__()

    async def execute(self) -> bool:
        if self.bot.supply_used > 30 and self.bot.supply_left < 8 and self.bot.supply_cap < 200:
            return True
        return False
    
    def debug_string(self) -> str:
        return "?TerranSupplyAuto"
        
class StrategyTerranSupply(Strategy, InterfaceBuildHelper):
    def __init__(self, bot : BotAIBase) -> None:
        super().__init__(bot)
        self.order = None
        acts: list[ActBase] = [
            ActSequence(ActCheckSupplyUsed(14), ActOrderBuild(UnitTypeId.SUPPLYDEPOT, self)),
            ActSequence(ActCheckSupplyUsed(21), ActOrderBuild(UnitTypeId.SUPPLYDEPOT, self)),
            ActSequence(ActCheckSupplyUsed(28), ActOrderBuild(UnitTypeId.SUPPLYDEPOT, self)),
            ActLoop(ActSequence(ActCheckTerranSupplyAuto(), ActAnd(ActOrderBuild(UnitTypeId.SUPPLYDEPOT, self), ActOrderBuild(UnitTypeId.SUPPLYDEPOT, self))))
        ]

        self.add_acts(acts)

    async def get_build_location(self, unit_type: UnitTypeId) -> Optional[Point2]:
        if self.bot.supply_cap > 50:
            return await self.get_build_location_later(unit_type)
        else:
            return await self.get_build_location_early(unit_type)

    async def get_build_location_early(self, unit_type: UnitTypeId) -> Optional[Point2]:
        base_location = self.bot.start_location
        region = self.bot.map_data.where_all(base_location)[0]
        choke_area = region.region_chokes[0]
        buildables = choke_area.buildables
        for point in buildables.points:
            position = await self.bot.find_placement(UnitTypeId.SUPPLYDEPOT, point)
            if position is not None:
                return position
        return None

    async def get_build_location_later(self, unit_type: UnitTypeId) -> Optional[Point2]:
        base_location = self.bot.start_location
        region = self.bot.map_data.where_all(base_location)[0]
        pre_location = region.region_chokes[0].center.towards(base_location, 6)
        position = await self.bot.find_placement(unit_type, pre_location.rounded, addon_place=True)
        if position is not None:
            return position
        
        return None

    def debug_string(self) -> str:
        return "TerranSupply"
