from typing import Optional
from bot.acts.act_check_unit import ActCheckBuildReady, ActCheckSupplyUsed
from bot.acts.act_order import ActOrderBuild, ActOrderBuildAddon, ActOrderTerranUnit
from bot.acts.act_flow_control import ActSequence
from bot.acts.interface_build_helper import InterfaceBuildHelper
from bot.bot_ai_base import BotAIBase
from bot.strategies.strategy import Strategy
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.unit import Unit


class StrategyTerranArmy(Strategy, InterfaceBuildHelper):
    def __init__(self, bot: BotAIBase) -> None:
        super().__init__(bot)

        self.act_order_marine = ActOrderTerranUnit(UnitTypeId.MARINE, 999)
        self.act_order_tank = ActOrderTerranUnit(UnitTypeId.SIEGETANK, 999)

        act_list = [
            ActSequence(ActCheckSupplyUsed(16), ActOrderBuild(UnitTypeId.BARRACKS, self), ActOrderBuildAddon(UnitTypeId.BARRACKSREACTOR), self.act_order_marine), 
            ActSequence(ActCheckSupplyUsed(21), ActOrderBuild(UnitTypeId.BARRACKS, self), ActOrderBuildAddon(UnitTypeId.BARRACKSREACTOR)), 
            ActSequence(ActCheckSupplyUsed(26), ActOrderBuild(UnitTypeId.FACTORY, self), ActOrderBuildAddon(UnitTypeId.FACTORYTECHLAB), self.act_order_tank), 
            ActSequence(ActCheckSupplyUsed(30), ActOrderBuild(UnitTypeId.BARRACKS, self), ActOrderBuildAddon(UnitTypeId.BARRACKSREACTOR)),
        ]

        self.add_acts(act_list)

        path = self.bot.map_data.pathfind(self.bot.start_location, self.bot.enemy_start_locations[0])
        self.rally_point_small = path[min(len(path) - 1, 40)]
        path = self.bot.map_data.pathfind(self.bot.start_location, self.bot.enemy_start_locations[0], large=True)
        self.rally_point_large = path[min(len(path), 36)]
        

    def debug_string(self) -> str:
        return "TerranArmy"

    async def step(self):
        """
        build_orders_new = []
        for build_order in self.build_orders:
            if build_order.out_build is not None:
                if build_order.out_build.type_id == UnitTypeId.BARRACKS:
                    build_order.out_build(AbilityId.RALLY_BUILDING, self.rally_point_small)
                elif build_order.out_build.type_id == UnitTypeId.FACTORY:
                    build_order.out_build(AbilityId.RALLY_BUILDING, self.rally_point_large)                   
            else:
                build_orders_new.append(build_order)
        self.build_orders = build_orders_new        
        """
        pass

    async def get_build_location(self, unit_type: UnitTypeId) -> Optional[Point2]:
        base_location = self.bot.start_location
        region = self.bot.map_data.where_all(base_location)[0]
        pre_location = region.region_chokes[0].center.towards(base_location, 6)
        position = await self.bot.find_placement(unit_type, pre_location.rounded, addon_place=True)
        if position is not None:
            return position
        
        return None

    def on_build_complete(self, unit: Unit):
        if unit.type_id == UnitTypeId.BARRACKS:
            unit(AbilityId.RALLY_BUILDING, self.rally_point_small)
        elif unit.type_id == UnitTypeId.FACTORY:
            unit(AbilityId.RALLY_BUILDING, self.rally_point_large)

