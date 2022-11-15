from typing import Callable
from bot.orders.order import Order
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit

"""
会产出新的单位的操作，主要是要跟踪哪个单位是新建造的
"""

class OrderUnit(Order):
    def __init__(self, unit_type : UnitTypeId, count : int, callback: Callable[[Unit], None] = None) -> None:
        super().__init__()

        self.target_type = unit_type
        self.target_positions : list[Point2] = []

        self.count_pending = count
        self.count_wip = 0
        self.priority = Order.prio_high

        self.callback = callback

    @property
    def has_requests(self) -> bool:
        return self.count_pending > 0

    @property
    def is_producing(self) -> bool:
        return self.count_wip > 0

    def update_count(self, count: int):
        self.count_pending = count

    async def produce(self) -> bool:
        if self.count_pending == 0:
            return False

        new_target_position = self.try_new_unit()
        if new_target_position is None:
            return False

        self.target_positions.append(new_target_position)
        self.count_wip = self.count_wip + 1
        self.count_pending = self.count_pending - 1
        return True
        
    def try_new_unit(self) -> Point2:
        return None

    def is_my_unit(self, unit: Unit) -> bool:
        return True

    def on_unit_create(self, unit : Unit) -> bool:
        if unit.type_id != self.target_type or not self.is_my_unit(unit):
            return False

        if self.callback:
            self.callback(unit)

        #todo 实现取消
        #assert(self.count_wip > 0)
        self.count_wip = self.count_wip - 1
        if self.count_pending == 0 and self.count_wip == 0:
            self.is_done = True

        return True
