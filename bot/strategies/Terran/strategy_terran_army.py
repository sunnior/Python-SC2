from typing import Optional
from bot.acts.act_order import ActOrderTerranUnit
from bot.bot_ai_base import BotAIBase
from bot.squads.squad_mining import SquadMining
from bot.strategies.strategy import Strategy
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit
from bot.acts.act_check_unit import ActCheckBuildReady
from bot.acts.act_flow_control import ActSequence
from bot.acts.act_base import ActBase
from bot.squads.squad_terran_army import SquadTerranArmy
from bot.orders.order import Order

class StrategyTerranArmy(Strategy):
    def __init__(self) -> None:
        super().__init__()

    def post_init(self, bot: BotAIBase):
        super().post_init(bot)

        path = self.bot.map_data.pathfind(self.bot.start_location, self.bot.enemy_start_locations[0])
        self.rally_point_small = path[min(len(path) - 1, 32)]
        path = self.bot.map_data.pathfind(self.bot.start_location, self.bot.enemy_start_locations[0], large=True)
        self.rally_point_large = path[min(len(path), 30)]
        self.new_units: list[Unit] = []

        self.setup_orders()

        scale = 1
        self.compositions = [
            (UnitTypeId.MARINE, 8 * scale),
            (UnitTypeId.MARAUDER, 4 * scale),
            (UnitTypeId.SIEGETANK, 1 * scale),
            (UnitTypeId.MEDIVAC, 1 * scale)
        ]
        self.squad_army_prepare: SquadTerranArmy = SquadTerranArmy(self.compositions)
        self.squad_army_attack: SquadTerranArmy = None

        self.add_squad(self.squad_army_prepare)

    def setup_orders(self):
        
        self.act_order_marine = ActOrderTerranUnit(UnitTypeId.MARINE, 999, self.on_order_unit_created)
        self.act_order_marauder = ActOrderTerranUnit(UnitTypeId.MARAUDER, 999, self.on_order_unit_created)
        self.act_order_tank = ActOrderTerranUnit(UnitTypeId.SIEGETANK, 999, self.on_order_unit_created)
        self.act_order_medivac = ActOrderTerranUnit(UnitTypeId.MEDIVAC, 999, self.on_order_unit_created)

        acts: list[ActBase] = [
            ActSequence(
                ActCheckBuildReady(UnitTypeId.BARRACKSREACTOR),
                self.act_order_marine
            ),
            ActSequence(
                ActCheckBuildReady(UnitTypeId.BARRACKSTECHLAB),
                self.act_order_marauder
            ),
            ActSequence(
                ActCheckBuildReady(UnitTypeId.FACTORYTECHLAB),
                self.act_order_tank
            ),
            ActSequence(
                ActCheckBuildReady(UnitTypeId.STARPORTREACTOR),
                self.act_order_medivac
            ),
        ]

        self.add_acts(acts)

    def debug_string(self) -> str:
        return "TerranArmy"

    async def step(self):
        self.step_squad()
        if self.squad_army_prepare.is_overloaded():
            self.squad_army_attack = self.squad_army_prepare
            self.squad_army_prepare = SquadTerranArmy(self.compositions)
            self.add_squad(self.squad_army_prepare)
            self.squad_army_attack.attack(self.bot.enemy_start_locations[0])

    def on_build_complete(self, unit: Unit):
        if unit.type_id == UnitTypeId.BARRACKS:
            unit(AbilityId.RALLY_BUILDING, self.rally_point_small)
        else:
            unit(AbilityId.RALLY_BUILDING, self.rally_point_large)

    def step_squad(self):
        for unit in self.new_units:
            self.squad_army_prepare.add_unit(unit)
        self.new_units.clear()

        self.adjust_army_order()

    def adjust_army_order(self):
        if not self.squad_army_prepare.cache_count_total:
            return
        
        order_types =  [
            (self.act_order_marine, UnitTypeId.MARINE), 
            (self.act_order_marauder, UnitTypeId.MARAUDER),
            (self.act_order_tank, UnitTypeId.SIEGETANK), 
            (self.act_order_medivac, UnitTypeId.MEDIVAC)
        ]

        for order, unit_type in order_types:
            if self.squad_army_prepare.is_short_of(unit_type):
                order.set_priority(Order.prio_high)
            else:
                order.set_priority(Order.prio_medium)

    def on_order_unit_created(self, unit: Unit):
        self.new_units.append(unit)