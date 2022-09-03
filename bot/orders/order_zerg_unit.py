from sc2.bot_ai import BotAI

from bot.orders.order_unit import OrderUnit
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit_command import UnitCommand

class OrderZergUnit(OrderUnit):
    def __init__(self, bot : BotAI, unit_type : UnitTypeId, count : int) -> None:
        super().__init__(unit_type, count)

        self.bot = bot
        unit_data = self.bot.game_data.units[self.target_type.value]
        cost = self.bot.game_data.calculate_ability_cost(unit_data.creation_ability)

        self.cost_vespene = cost.vespene
        self.cost_minerals = cost.minerals
        self.cost_supply = self.bot.calculate_supply_cost(self.target_type)

    def try_new_unit(self) -> Point2:
        if self.bot.supply_left < self.cost_supply:
            return

        if self.bot.vespene >= self.cost.vespene and self.bot.minerals >= self.cost.minerals:                    
            for unit in self.bot.units:
                if unit.type_id == UnitTypeId.LARVA:
                    if unit.train(self.target_type):
                        print("Unit new", unit.position)
                        return unit.position
