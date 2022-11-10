from typing import Optional
from bot.acts.act_base import ActBase
from bot.acts.act_check_unit import ActCheckBuildReady, ActCheckSupplyUsed
from bot.acts.act_flow_control import ActAnd, ActLoop, ActSequence
from bot.acts.act_order import ActOrderBuild, ActOrderBuildAddon, ActOrderTerranUnit, ActOrderUpgrade
from bot.bot_ai_base import BotAIBase
from bot.city.city import City
from bot.orders.interface_build_helper import InterfaceBuildHelper
from bot.strategies.strategy import Strategy
from bot.strategies.Terran.strategy_terran_army import StrategyTerranArmy
from bot.strategies.Terran.strategy_terran_mining import StrategyTerranMining
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
        self.is_choke_open = 2

    async def get_build_position(self, unit_type: UnitTypeId) -> Optional[Point2]:
        is_lock_position = True
        is_lock_addon = False
        if unit_type == UnitTypeId.SUPPLYDEPOT:
            position = await self.get_supplydepot_position(unit_type)
        elif unit_type in [UnitTypeId.BARRACKS, UnitTypeId.FACTORY]:
            position = await self.get_army_building_position(unit_type)
            is_lock_addon = True
        elif unit_type == UnitTypeId.COMMANDCENTER:
            position = await self.bot.get_next_expansion()
            is_lock_position = False

        if position and is_lock_position:
            main_city: City = self.bot.cities[0]
            unit_data = self.bot.game_data.units[unit_type.value]
            radius = unit_data.footprint_radius
            position_origin = position.offset(Point2((-radius, -radius))).rounded
            main_city.lock_positions(position_origin, Point2((int(radius * 2), int(radius * 2))))
            self.reserve_positions.append(position_origin)
            if is_lock_addon:
                main_city.lock_positions(position_origin.offset(Point2((int(radius * 2), 0))), Point2((2, 2)))

        return position

    async def get_supplydepot_position(self, unit_type: UnitTypeId):
        main_city: City = self.bot.cities[0]
        if self.bot.supply_used < 30:
            position = await main_city.get_placement_near_choke(unit_type)
        else:
            position = await main_city.get_placement_far_choke(unit_type)
        return position
        
    async def get_army_building_position(self, unit_type: UnitTypeId):
        main_city: City = self.bot.cities[0]
        if self.is_choke_open:
            return await main_city.get_placement_near_choke(unit_type, 0, True)
        else:
            return await main_city.get_placement_near_base(unit_type, 25, True)

    def on_build_complete(self, unit: Unit, worker_tag: int):
        is_lock_position = True
        if unit.type_id == UnitTypeId.SUPPLYDEPOT:
            unit(AbilityId.MORPH_SUPPLYDEPOT_LOWER)
        elif unit.type_id in [ UnitTypeId.BARRACKS, UnitTypeId.FACTORY ]:
            if self.is_choke_open:
                #todo 
                self.is_choke_open = self.is_choke_open - 1
            self.strategy_army.on_build_complete(unit)
        elif unit.type_id == UnitTypeId.COMMANDCENTER:
            self.strategy_mining.create_squad_mining(unit)
            is_lock_position = False
        elif unit.type_id == UnitTypeId.REFINERY:
            is_lock_position = False

        if is_lock_position:
            main_city: City = self.bot.cities[0]
            unit_data = self.bot.game_data.units[unit.type_id.value]
            radius = unit_data.footprint_radius        
            position_origin = unit.position.offset(Point2((-radius, -radius))).rounded
            self.reserve_positions.remove(position_origin)
            main_city.unlock_positions(position_origin, Point2((int(radius * 2), int(radius * 2))))

        self.strategy_mining.add_worker(worker_tag)

    def on_addon_complete(self, unit: Unit):
        pass

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
        
        self.strategy_mining = StrategyTerranMining()
        self.strategy_army = StrategyTerranArmy()

        self.add_sub_strategy(self.strategy_mining)
        self.add_sub_strategy(self.strategy_army)

        self.build_helper = BuildHelperTerranPigStart(self.bot, self.strategy_mining, self.strategy_army)

        self.setup_build_order()

    def setup_build_order(self):
        acts: list[ActBase] = [
            ActSequence(
                ActCheckBuildReady(UnitTypeId.BARRACKS),
                ActOrderTerranUnit(UnitTypeId.REAPER, 1),
                ActOrderTerranUnit(UnitTypeId.MARINE, 999)
            ),
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
                ActCheckSupplyUsed(20),
                ActAnd(
                    ActSequence(
                        ActOrderBuild(UnitTypeId.BARRACKS, self.build_helper),
                        ActOrderBuildAddon(UnitTypeId.BARRACKSTECHLAB, self.build_helper)
                    ),
                    ActSequence(
                        ActOrderBuild(UnitTypeId.BARRACKS, self.build_helper),
                        ActOrderBuildAddon(UnitTypeId.BARRACKSTECHLAB, self.build_helper)
                    )
                ),
                ActAnd(
                    ActOrderUpgrade(UpgradeId.STIMPACK),
                    ActOrderUpgrade(UpgradeId.SHIELDWALL)
                )                
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

    def debug_string(self) -> str:
        return "TerranPigDiamond"