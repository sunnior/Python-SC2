from typing import Optional
from bot.acts.act_base import ActBase
from bot.acts.act_check_unit import ActCheckSupplyUsed
from bot.acts.act_order import ActOrderBuild
from bot.acts.act_flow_control import ActLoop, ActSequence, ActAnd
from bot.orders.interface_build_helper import InterfaceBuildHelper
from bot.bot_ai_base import BotAIBase
from bot.city.city import City
from bot.squads.squad_mining import SquadMining
from bot.strategies.strategy import Strategy
from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit

class ActCheckTerranSupplyAuto(ActBase):
    def __init__(self):
        super().__init__()

    async def execute(self) -> bool:
        if self.bot.supply_used > 30 and self.bot.supply_left < 8 and self.bot.supply_cap < 200:
            return True
        return False
    
    def debug_string(self) -> str:
        return "?TerranSupplyAuto"
        
class BuildHelperTerranSupply(InterfaceBuildHelper):
    def __init__(self, bot: BotAIBase):
        self.bot = bot
        self.reserve_positions: list[Point2] = []

    async def get_build_position(self, unit_type: UnitTypeId) -> Optional[Point2]:
        return await self.get_build_location_early(unit_type)

    async def get_build_location_early(self, unit_type: UnitTypeId) -> Optional[Point2]:
        main_city: City = self.bot.cities[0]
        position = await main_city.get_placement_near_choke(unit_type)
        if position:
            position_origin = position.offset(Point2((-1, -1))).rounded
            main_city.lock_positions(position_origin, Point2((2, 2)))
            self.reserve_positions.append(position_origin)

        return position

    def on_build_complete(self, unit: Unit, worker_tag: int):
        position_origin = unit.position.offset(Point2((-1, -1))).rounded    
        self.reserve_positions.remove(position_origin)
        main_city: City = self.bot.cities[0]
        main_city.unlock_positions(position_origin, Point2((2, 2)))

        for squad in self.bot.squads:
            if isinstance(squad, SquadMining):
                squad.add_worker(self.bot.workers.find_by_tag(worker_tag))
                break

        unit(AbilityId.MORPH_SUPPLYDEPOT_LOWER)
        
    def get_worker(self) -> Optional[Unit]:
        for squad in self.bot.squads:
            if isinstance(squad, SquadMining):
                worker_tag = squad.remove_worker()
                break

        if worker_tag:
            return self.bot.workers.find_by_tag(worker_tag)

        return None

class StrategyTerranSupply(Strategy):
    def __init__(self) -> None:
        super().__init__()

    def post_init(self, bot: BotAIBase):
        super().post_init(bot)
        self.build_helper = BuildHelperTerranSupply(self.bot)
        
        self.order = None
        acts: list[ActBase] = [
            ActSequence(ActCheckSupplyUsed(14), ActOrderBuild(UnitTypeId.SUPPLYDEPOT, self.build_helper)),
            ActSequence(ActCheckSupplyUsed(21), ActOrderBuild(UnitTypeId.SUPPLYDEPOT, self.build_helper)),
            ActSequence(ActCheckSupplyUsed(28), ActOrderBuild(UnitTypeId.SUPPLYDEPOT, self.build_helper)),
            ActLoop(ActSequence(ActCheckTerranSupplyAuto(), ActAnd(ActOrderBuild(UnitTypeId.SUPPLYDEPOT, self.build_helper), ActOrderBuild(UnitTypeId.SUPPLYDEPOT, self.build_helper))))
        ]

        self.add_acts(acts)

    def debug_string(self) -> str:
        return "TerranSupply"
