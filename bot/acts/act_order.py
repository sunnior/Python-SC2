from typing import Callable
from numpy import true_divide
from bot.acts.act_base import ActBase
from bot.orders.interface_build_helper import InterfaceBuildHelper
from bot.bot_ai_base import BotAIBase
from bot.orders.order import Order
from bot.orders.order_addon import OrderAddon
from bot.orders.order_build import OrderBuild
from bot.orders.order_build_woker import OrderBuildWorker
from bot.orders.order_terran_unit import OrderTerranUnit
from bot.orders.order_upgrade import OrderUpgrade
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import Unit

class ActOrder(ActBase):
    def __init__(self):
        super().__init__()
        self.order: Order = None

    def set_priority(self, priority: int):
        if self.order:
            self.order.priority = priority

class ActOrderBuild(ActOrder):
    def __init__(self, build_type: UnitTypeId, build_helper: InterfaceBuildHelper, callback: Callable[[Unit], None] = None):
        super().__init__()
        self.build_type = build_type
        self.order: Order = None
        self.build_helper = build_helper
        self.callback = callback

    def on_added(self, bot: BotAI):
        super().on_added(bot)
        self.order = OrderBuildWorker(self.build_type, self.build_helper, self.callback)
        self.bot.producer.add_order(self.order)

    async def execute(self) -> bool:
        if self.order.is_done:
            return True
    
        return False

    def debug_string(self) -> str:
        if self.order:
            return self.order.debug_string()
        else:
            return "$build-" + str(self.build_type).replace("UnitTypeId.", "")

class ActOrderTerranUnit(ActOrder):
    def __init__(self, unit_type: UnitTypeId, count: int, callback: Callable[[Unit], None] = None):
        super().__init__()

        self.unit_type = unit_type
        self.count = count
        self.order: OrderTerranUnit = None
        self.callback = callback

    def update_count(self, count: int):
        self.count = count
        if self.order:
            self.order.update_count(count)

    def on_added(self, bot: BotAI):
        super().on_added(bot)

        self.order = OrderTerranUnit(self.unit_type, self.count, self.callback)
        self.bot.producer.add_order(self.order)
            
    async def execute(self) -> bool:
        if self.order.is_done:
            return True
        else:
            return False

    def debug_string(self) -> str:
        if self.order:
            return self.order.debug_string()
        else:
            return "$Unit-" + str(self.unit_type).replace("UnitTypeId.", "")             
        
class ActOrderBuildAddon(ActOrder):
    def __init__(self, unit_type: UnitTypeId, build_helper: InterfaceBuildHelper, callback: Callable[[Unit], None] = None):
        super().__init__()
        self.order = None
        self.unit_type = unit_type
        self.build_helper = build_helper
        self.callback = callback

    def on_added(self, bot: BotAI):
        super().on_added(bot)

        self.order = OrderAddon(self.unit_type, self.build_helper, self.callback)
        self.bot.producer.add_order(self.order)

    async def execute(self) -> bool:
        return self.order.is_done    

    def debug_string(self) -> str:
        if self.order:
            return self.order.debug_string()
        else:
            return "$Addon-" + str(self.unit_type).replace("UnitTypeId.", "")

class ActOrderUpgrade(ActOrder):
    def __init__(self, upgrade_id: UpgradeId):
        super().__init__()
        self.upgrade_id = upgrade_id
        self.order = None

    def on_added(self, bot: BotAI):
        super().on_added(bot)
        self.order = OrderUpgrade(self.upgrade_id)
        self.bot.producer.add_order(self.order)

    async def execute(self) -> bool:
        return self.order.is_done    

    def debug_string(self) -> str:
        if self.order:
            return self.order.debug_string()
        else:
            return "$Upgrade-" +str(self.upgrade_id).replace("UpgradeId.", "")