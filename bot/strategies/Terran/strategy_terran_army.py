from typing import Optional
from bot.acts.act_check_unit import ActCheckBuildReady, ActCheckSupplyUsed
from bot.acts.act_order import ActOrderBuild, ActOrderBuildAddon, ActOrderTerranUnit, ActOrderUpgrade
from bot.acts.act_flow_control import ActSequence
from bot.orders.interface_build_helper import InterfaceBuildHelper
from bot.bot_ai_base import BotAIBase
from bot.city.city import City
from bot.squads.squad_mining import SquadMining
from bot.strategies.strategy import Strategy
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2
from sc2.unit import Unit

class BuildHelperTerranArmy(InterfaceBuildHelper):
    def __init__(self, bot: BotAIBase, owner):
        self.bot = bot
        self.owner = owner
        self.reserve_positions: list[Point2] = []
        self.build_count = 0

    async def get_build_position(self, unit_type: UnitTypeId) -> Optional[Point2]:
        main_city: City = self.bot.cities[0]
        self.build_count = self.build_count + 1
        if self.build_count > 2:
            position = await main_city.get_placement_near_base(unit_type, 25, True)
        else:
            position = await main_city.get_placement_near_choke(unit_type, 0, True)

        if position:
            position_origin = position.offset(Point2((-1, -1))).rounded
            
            unit_data = self.bot.game_data.units[unit_type.value]
            size = unit_data.footprint_radius * 2

            main_city.lock_positions(position_origin, Point2((int(size), int(size))))
            self.reserve_positions.append(position_origin)

            addon_position = position_origin.offset(Point2((int(size), 0)))
            main_city.lock_positions(addon_position, Point2((2, 2)))
            self.reserve_positions.append(addon_position)

        return position
        
    def get_worker(self) -> Optional[Unit]:
        for squad in self.bot.squads:
            if isinstance(squad, SquadMining):
                worker_tag = squad.remove_worker()
                break

        if worker_tag:
            return self.bot.workers.find_by_tag(worker_tag)

        return None

    def on_build_complete(self, unit: Unit, worker_tag: int):
        unit_data = self.bot.game_data.units[unit.type_id.value]
        radius = unit_data.footprint_radius
        position_origin = unit.position.offset(Point2((-radius, -radius))).rounded    
        self.reserve_positions.remove(position_origin)
        main_city: City = self.bot.cities[0]
        main_city.unlock_positions(position_origin, Point2((int(radius * 2), int(radius * 2))))
        self.owner.on_build_complete(unit)
        
        for squad in self.bot.squads:
            if isinstance(squad, SquadMining):
                squad.add_worker(self.bot.workers.find_by_tag(worker_tag))
                break

    def on_addon_complete(self, unit: Unit):
        unit_data = self.bot.game_data.units[unit.type_id.value]
        radius = unit_data.footprint_radius
        position_origin = unit.position.offset(Point2((-radius, -radius))).rounded    
        self.reserve_positions.remove(position_origin)
        main_city: City = self.bot.cities[0]
        main_city.unlock_positions(position_origin, Point2((int(radius * 2), int(radius * 2))))    

class StrategyTerranArmy(Strategy):
    def __init__(self) -> None:
        super().__init__()

    def post_init(self, bot: BotAIBase):
        super().post_init(bot)
        self.build_helper = BuildHelperTerranArmy(bot, self)

        self.act_order_marine = ActOrderTerranUnit(UnitTypeId.MARINE, 999)
        self.act_order_tank = ActOrderTerranUnit(UnitTypeId.SIEGETANK, 999)

        act_list = [
            ActSequence(ActCheckSupplyUsed(16), ActOrderBuild(UnitTypeId.BARRACKS, self.build_helper), ActOrderBuildAddon(UnitTypeId.BARRACKSREACTOR, self.build_helper), self.act_order_marine), 
            ActSequence(ActCheckSupplyUsed(21), 
                        ActOrderBuild(UnitTypeId.BARRACKS, self.build_helper), 
                        ActOrderBuildAddon(UnitTypeId.BARRACKSTECHLAB, self.build_helper), 
                        ActOrderUpgrade(UpgradeId.STIMPACK)), 
            ActSequence(ActCheckSupplyUsed(26), ActOrderBuild(UnitTypeId.FACTORY, self.build_helper), ActOrderBuildAddon(UnitTypeId.FACTORYTECHLAB, self.build_helper), self.act_order_tank), 
            ActSequence(ActCheckSupplyUsed(30), ActOrderBuild(UnitTypeId.BARRACKS, self.build_helper), ActOrderBuildAddon(UnitTypeId.BARRACKSREACTOR, self.build_helper)),
        ]

        self.add_acts(act_list)

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

