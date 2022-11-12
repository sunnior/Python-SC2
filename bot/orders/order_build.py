from bot.orders.order import Order
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit

class OrderBuild(Order):
    def __init__(self) -> None:
        super().__init__()
        self.priority = Order.prio_highest

    def on_building_construction_complete(self, unit: Unit):
        return False

    def on_unit_type_changed(self, unit: Unit, previous_type: UnitTypeId):
        return False

    def debug_string(self) -> str:
        return "OrderBuild"
