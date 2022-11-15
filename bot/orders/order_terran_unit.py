from distutils.command.build import build

from typing import Callable, Optional
from sc2.bot_ai import BotAI
from bot.orders.order import Order
from bot.orders.order_unit import OrderUnit
from sc2.data import Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.dicts.unit_trained_from import UNIT_TRAINED_FROM
from sc2.dicts.unit_train_build_abilities import TRAIN_INFO

class OrderTerranUnit(OrderUnit):
    def __init__(self, unit_type : UnitTypeId, count : int, callback: Callable[[Unit], None] = None) -> None:
        super().__init__(unit_type, count, callback)
        self.builder_types = list(UNIT_TRAINED_FROM[unit_type])

    def on_added(self, bot: BotAI):
        super().on_added(bot)

        unit_data = self.bot.game_data.units[self.target_type.value]
        cost = self.bot.game_data.calculate_ability_cost(unit_data.creation_ability)

        self.cost_vespene = cost.vespene
        self.cost_minerals = cost.minerals
        self.cost_supply = self.bot.calculate_supply_cost(self.target_type)

    def on_removed(self):
        if self.count_wip:
            #todo cancel build progress
            pass
        pass

    def is_my_unit(self, unit: Unit) -> bool:
        if unit.is_carrying_vespene:
            #todo 研究下这个是为啥
            return False
        
        return True

    def try_new_unit(self) -> Optional[Point2]:
        builders: list[Unit] = []
        for builder in self.bot.structures:
            if builder.type_id not in self.builder_types:
                continue

            if builder.build_progress != 1:
                continue
            
            if builder.has_add_on:
                if len(builder.orders) and builder.orders[0].ability.id in [ AbilityId.BUILD_REACTOR, AbilityId.BUILD_TECHLAB ]:
                    #如果还有build reactor的残留，那就不要，这个api导致的，没办法
                    continue

            order_cap = 1
            if builder.has_reactor:                
                order_cap = 2
        
            if len(builder.orders) == order_cap:
                continue

            is_prefer_builder = True
            if "requires_techlab" in TRAIN_INFO[builder.type_id][self.target_type]:
                if not builder.has_techlab:
                    continue
            else:
                if builder.has_techlab:
                    is_prefer_builder = False

            if is_prefer_builder:
                builders.insert(0, builder)
            else:
                builders.append(builder)

        for builder in builders:
            if builder.train(self.target_type):
                return builder.position

    def debug_string(self) -> str:
        return "$TerranUnit-" + str(self.target_type).replace("UnitTypeId.", "") + "-" + str(self.count_pending) + "-" + str(self.count_wip) + self.debug_get_progress_char()