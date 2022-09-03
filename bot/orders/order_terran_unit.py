from distutils.command.build import build

from typing import Optional
from sc2.bot_ai import BotAI
from bot.orders.order import Order
from bot.orders.order_unit import OrderUnit
from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit

class OrderTerranUnit(OrderUnit):
    def __init__(self, unit_type : UnitTypeId, count : int) -> None:
        super().__init__(unit_type, count)
        self.builder_types = []
        if unit_type == UnitTypeId.SCV:
            self.builder_types = [UnitTypeId.COMMANDCENTER, UnitTypeId.ORBITALCOMMAND, UnitTypeId.PLANETARYFORTRESS]
        elif unit_type == UnitTypeId.MARINE:
            #todo techlab有可能用来生产其他的
            self.builder_types = [UnitTypeId.BARRACKS]
        elif unit_type == UnitTypeId.SIEGETANK:
            self.builder_types = [UnitTypeId.FACTORY]

    def on_submit(self, bot: BotAI):
        super().on_submit(bot)

        unit_data = self.bot.game_data.units[self.target_type.value]
        cost = self.bot.game_data.calculate_ability_cost(unit_data.creation_ability)

        self.cost_vespene = cost.vespene
        self.cost_minerals = cost.minerals
        self.cost_supply = self.bot.calculate_supply_cost(self.target_type)

    def is_my_unit(self, unit: Unit) -> bool:
        if unit.is_carrying_vespene:
            #todo 研究下这个是为啥
            return False
        
        return True

    def try_new_unit(self) -> Optional[Point2]:
        builders = None
        for builder in self.bot.structures:
            if builder.type_id not in self.builder_types:
                continue

            if builder.build_progress != 1:
                continue
            
            order_cap = 1
            if builder.type_id == UnitTypeId.BARRACKS:
                add_on_tag = builder.add_on_tag
                if add_on_tag != 0:
                   add_on = self.bot.structures.find_by_tag(add_on_tag)
                   if add_on.type_id == UnitTypeId.BARRACKSREACTOR:
                        #todo 缓存？
                        order_cap = 2
        
            if len(builder.orders) == order_cap:
                continue

            if builder.train(self.target_type):
                return builder.position

    def debug_string(self) -> str:
        return "$TerranUnit-" + str(self.target_type).replace("UnitTypeId.", "") + "-" + str(self.count_pending) + "-" + str(self.count_wip) + self.debug_get_progress_char()