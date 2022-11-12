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
        self.rally_point_small = path[min(len(path) - 1, 40)]
        path = self.bot.map_data.pathfind(self.bot.start_location, self.bot.enemy_start_locations[0], large=True)
        self.rally_point_large = path[min(len(path), 36)]

        self.setup_orders()

    def start(self):
        super().start()
        com_marine = 8
        com_marauder = 4
        com_tanks = 1
        com_medivac = 1
        com_total = float(com_tanks + com_marauder + com_marine + com_medivac)
        compositions = [
            (UnitTypeId.MARINE, com_marine / com_total),
            (UnitTypeId.MARAUDER, com_marauder / com_total),
            (UnitTypeId.SIEGETANK, com_tanks / com_total),
            (UnitTypeId.MEDIVAC, com_medivac / com_total)
        ]
        self.squad_army: SquadTerranArmy = SquadTerranArmy(compositions)
        self.add_squad(self.squad_army)

    def setup_orders(self):
        
        self.act_order_marine = ActOrderTerranUnit(UnitTypeId.MARINE, 999)
        self.act_order_marauder = ActOrderTerranUnit(UnitTypeId.MARAUDER, 999)
        self.act_order_tank = ActOrderTerranUnit(UnitTypeId.SIEGETANK, 999)
        self.act_order_medivac = ActOrderTerranUnit(UnitTypeId.MEDIVAC, 999)

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

    def on_build_complete(self, unit: Unit):
        if unit.type_id == UnitTypeId.BARRACKS:
            unit(AbilityId.RALLY_BUILDING, self.rally_point_small)
        else:
            unit(AbilityId.RALLY_BUILDING, self.rally_point_large)

    def step_squad(self):
        for act_order in [ self.act_order_marine, self.act_order_marauder, self.act_order_tank, self.act_order_medivac ]:
            for unit in act_order.out_units:
                self.squad_army.add_unit(unit)

        self.adjust_army_order()

    def adjust_army_order(self):
        if not self.squad_army.cache_count_total:
            return
        
        order_types =  [
            (self.act_order_marine, UnitTypeId.MARINE), 
            (self.act_order_marauder, UnitTypeId.MARAUDER),
            (self.act_order_tank, UnitTypeId.SIEGETANK), 
            (self.act_order_medivac, UnitTypeId.MEDIVAC)
        ]

        for order, unit_type in order_types:
            if self.squad_army.is_short_of(unit_type):
                order.set_priority(Order.prio_high)
            else:
                order.set_priority(Order.prio_medium)
