from typing import Optional
from bot.acts.act_base import ActBase
from bot.acts.act_check_unit import ActCheckSupplyUsed
from bot.acts.act_flow_control import ActAnd, ActLoop, ActSequence
from bot.acts.act_order import ActOrderBuild, ActOrderBuildAddon, ActOrderTerranUnit, ActOrderUpgrade
from bot.bot_ai_base import BotAIBase
from bot.city.city import City
from bot.orders.interface_build_helper import InterfaceBuildHelper
from bot.squads.squad_command_center import SquadCommandCenter
from bot.strategies.strategy import Strategy
from bot.strategies.Terran.strategy_terran_army import StrategyTerranArmy
from bot.strategies.Terran.strategy_terran_mining import StrategyTerranMining
from bot.strategies.Terran.strategy_terran_scout import StrategyTerranScout

from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2
from sc2.unit import Unit

class BuildHelperTerranPigStart(InterfaceBuildHelper):
    def __init__(self, bot: BotAIBase, strategy_mining: StrategyTerranMining, strategy_army: StrategyTerranArmy):
        self.bot = bot
        self.reserve_positions: list[Point2] = []
        self.strategy_mining: StrategyTerranMining = strategy_mining
        self.strategy_army: StrategyTerranArmy = strategy_army
        self.is_choke_open = True

    async def get_build_position(self, unit_type: UnitTypeId) -> Optional[Point2]:
        is_lock_position = True
        is_lock_addon = False
        if unit_type == UnitTypeId.SUPPLYDEPOT:
            position = await self.get_supplydepot_position(unit_type)
        elif unit_type in [UnitTypeId.BARRACKS, UnitTypeId.FACTORY, UnitTypeId.STARPORT]:
            position = await self.get_army_building_position(unit_type)
            is_lock_addon = True
        elif unit_type == UnitTypeId.COMMANDCENTER:
            position = self.get_next_expansion()
            is_lock_position = False

        if position and is_lock_position:
            main_city: City = self.bot.cities[0]
            unit_data = self.bot.game_data.units[unit_type.value]
            radius = unit_data.footprint_radius
            position_origin = position.offset(Point2((-radius, -radius))).rounded
            main_city.lock_positions(position_origin, Point2((int(radius * 2), int(radius * 2))))
            self.reserve_positions.append(position_origin)
            if is_lock_addon:
                position_addon = position_origin.offset(Point2((int(radius * 2), 0)))
                self.reserve_positions.append(position_addon)
                main_city.lock_positions(position_addon, Point2((2, 2)))

        return position

    async def get_supplydepot_position(self, unit_type: UnitTypeId):
        main_city: City = self.bot.cities[0]
        if self.bot.supply_used < 30:
            position = await main_city.get_placement_in_choke(unit_type)
        else:
            position = await main_city.get_placement_in_back(unit_type)
            if not position:
                position = await main_city.get_placement_in_base(unit_type)
        return position
        
    async def get_army_building_position(self, unit_type: UnitTypeId):
        main_city: City = self.bot.cities[0]
        if self.is_choke_open:
            #todo 
            self.is_choke_open = False
            return await main_city.get_placement_in_choke(unit_type, True)
        else:
            return await main_city.get_placement_in_base(unit_type, True)

    def get_next_expansion(self):
        main_city: City = self.bot.cities[0]
        region = main_city.region
        scan_regions = [ region_nbr[0] for region_nbr in region.regions_nbr ]
        scaned_regions = [ region.region_id ]
        next_scan_regions = []
        expansion = None
        while len(scan_regions):
            scaned_regions = scaned_regions + scan_regions
            for i_region_id in scan_regions:
                i_region = self.bot.map_tool.regions[i_region_id]
                if i_region.townhall_location:
                    expansion = i_region.townhall_location
                    return expansion
                
                for region_nbr in i_region.regions_nbr:
                    if region_nbr[0] not in scaned_regions:
                        next_scan_regions.append(region_nbr[0])
                
            next_scan_regions, scan_regions = scan_regions, next_scan_regions   
            next_scan_regions.clear()        
        return expansion

    def on_build_complete(self, unit: Unit, worker_tag: int):
        is_lock_position = True
        if unit.type_id == UnitTypeId.SUPPLYDEPOT:
            unit(AbilityId.MORPH_SUPPLYDEPOT_LOWER)
        elif unit.type_id in [ UnitTypeId.BARRACKS, UnitTypeId.FACTORY, UnitTypeId.STARPORT ]:
            self.strategy_army.on_build_complete(unit)
        elif unit.type_id == UnitTypeId.COMMANDCENTER:
            self.strategy_mining.create_squad_mining(unit)
            is_lock_position = False
        elif unit.type_id in [ UnitTypeId.REFINERY, UnitTypeId.ORBITALCOMMAND ]:
            is_lock_position = False

        if is_lock_position:
            main_city: City = self.bot.cities[0]
            unit_data = self.bot.game_data.units[unit.type_id.value]
            radius = unit_data.footprint_radius        
            position_origin = unit.position.offset(Point2((-radius, -radius))).rounded
            self.reserve_positions.remove(position_origin)
            main_city.unlock_positions(position_origin, Point2((int(radius * 2), int(radius * 2))))

        if worker_tag:
            self.strategy_mining.add_worker_tag(worker_tag)

    def on_addon_complete(self, unit: Unit):
        self.on_build_complete(unit, None)

    def get_worker(self, near: Point2) -> Optional[Unit]:
        return self.strategy_mining.remove_worker(near)

    def get_vespene_geyser(self) -> Optional[int]:
        return self.strategy_mining.get_vespene_geyser()

class ActCheckTerranSupplyAuto(ActBase):
    def __init__(self):
        super().__init__()

    async def execute(self) -> bool:
        if self.bot.supply_used > 30 and self.bot.supply_left < 8 and self.bot.supply_cap < 200:
            return True
        return False
    
    def debug_string(self) -> str:
        return "?TerranSupplyAuto"
        
class StrategyTerranPigStart(Strategy):
    def __init__(self) -> None:
        super().__init__()

    def post_init(self, bot: BotAIBase):
        super().post_init(bot)
        
        self.squad_cc = SquadCommandCenter()
        self.add_squad(self.squad_cc)

        self.strategy_mining = StrategyTerranMining(self.squad_cc)
        self.strategy_army = StrategyTerranArmy()
        self.strategy_scout = StrategyTerranScout()

        self.add_sub_strategy(self.strategy_mining)
        self.add_sub_strategy(self.strategy_army)
        self.add_sub_strategy(self.strategy_scout)

        self.setup_build_order()

    def setup_build_order(self):
        self.build_helper = BuildHelperTerranPigStart(self.bot, self.strategy_mining, self.strategy_army)

        acts: list[ActBase] = [
            ActSequence(
                ActCheckSupplyUsed(14), 
                ActOrderBuild(UnitTypeId.SUPPLYDEPOT, self.build_helper),
                ActCheckSupplyUsed(20), 
                ActOrderBuild(UnitTypeId.SUPPLYDEPOT, self.build_helper),
            ),
            ActSequence(
                ActCheckSupplyUsed(16), 
                ActAnd(
                    ActSequence(
                        ActOrderBuild(UnitTypeId.BARRACKS, self.build_helper), 
                        ActOrderTerranUnit(UnitTypeId.REAPER, 1, self.on_reaper_created),
                        ActOrderBuildAddon(UnitTypeId.BARRACKSREACTOR, self.build_helper)
                    ),
                    ActOrderBuild(UnitTypeId.REFINERY, self.build_helper)
                ),
            ),
            ActSequence(
                ActCheckSupplyUsed(19),
                ActAnd(
                    ActOrderBuildAddon(UnitTypeId.ORBITALCOMMAND, self.build_helper),
                    ActOrderBuild(UnitTypeId.COMMANDCENTER, self.build_helper)
                )
            ),
            ActSequence(
                ActCheckSupplyUsed(22),
                ActAnd(
                    ActSequence(
                        ActOrderBuild(UnitTypeId.BARRACKS, self.build_helper),
                        ActOrderBuildAddon(UnitTypeId.BARRACKSTECHLAB, self.build_helper)
                    ),
                    ActSequence(
                        ActOrderBuild(UnitTypeId.BARRACKS, self.build_helper),
                        ActOrderBuildAddon(UnitTypeId.BARRACKSTECHLAB, self.build_helper)
                    ),
                    ActOrderBuild(UnitTypeId.REFINERY, self.build_helper)
                ),
                ActAnd(
                    ActOrderUpgrade(UpgradeId.STIMPACK),
                    ActOrderUpgrade(UpgradeId.SHIELDWALL)
                )                
            ),
            ActSequence(
                ActCheckSupplyUsed(35),
                ActOrderBuild(UnitTypeId.FACTORY, self.build_helper),
                ActAnd(
                    ActSequence(
                        ActOrderBuild(UnitTypeId.STARPORT, self.build_helper),
                        ActOrderBuildAddon(UnitTypeId.STARPORTREACTOR, self.build_helper),
                    ),
                    ActOrderBuildAddon(UnitTypeId.FACTORYTECHLAB, self.build_helper),
                    ActOrderBuild(UnitTypeId.REFINERY, self.build_helper)
                ),
                ActCheckSupplyUsed(90),
                ActAnd(
                    ActSequence(
                        ActOrderBuild(UnitTypeId.FACTORY, self.build_helper),
                        ActOrderBuildAddon(UnitTypeId.FACTORYTECHLAB, self.build_helper),
                    ),
                    ActSequence(
                        ActOrderBuild(UnitTypeId.BARRACKS, self.build_helper),
                        ActOrderBuildAddon(UnitTypeId.BARRACKSREACTOR, self.build_helper),
                    ),
                    ActOrderBuild(UnitTypeId.REFINERY, self.build_helper)
                ),
            ),
            ActLoop(
                ActSequence(
                    ActCheckTerranSupplyAuto(), 
                    ActAnd(
                        ActOrderBuild(UnitTypeId.SUPPLYDEPOT, self.build_helper), 
                        ActOrderBuild(UnitTypeId.SUPPLYDEPOT, self.build_helper)
                    )
                )
            )
        ]

        self.add_acts(acts)

    async def step(self):
        await super().step()
        #todo 临时
        #if self.strategy_scout.is_empty():
        #    self.strategy_scout.add_unit(self.strategy_mining.remove_worker(self.bot.townhalls[0].position))

    def on_reaper_created(self, unit: Unit):
        self.strategy_scout.add_unit(unit)

    def debug_string(self) -> str:
        return "TerranPigDiamond"