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
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import Unit

class ActOrder(ActBase):
    def __init__(self):
        super().__init__()
        

class ActOrderBuild(ActOrder):
    def __init__(self, build_type: UnitTypeId, build_helper: InterfaceBuildHelper):
        super().__init__()
        self.build_type = build_type
        self.order: Order = None
        self.build_helper = build_helper

    async def create_order(self):
        self.order = OrderBuildWorker(self.build_type, self.build_helper)
        self.order.reserve()
        self.bot.producer.submit(self.order)

    async def start(self):
        await super().start()
        await self.create_order()

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
    def __init__(self, unit_type: UnitTypeId, count: int):
        super().__init__()

        self.unit_type = unit_type
        self.count = count
        self.order: OrderTerranUnit = None
        self.out_units: list[Unit] = []

    async def start(self):
        await super().start()
        self.order = OrderTerranUnit(self.unit_type, self.count)
        self.bot.producer.submit(self.order)

    async def stop(self):
        await super().stop()     
        if not self.order.is_done:
            self.bot.producer.unsubmit(self.order)
            self.order = None
            
    async def execute(self) -> bool:
        self.out_units = self.order.out_units
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
    def __init__(self, unit_type: UnitTypeId, build_helper: InterfaceBuildHelper):
        super().__init__()
        self.order = None
        self.unit_type = unit_type
        self.build_helper = build_helper

    async def start(self):
        await super().start()
        self.order = OrderAddon(self.unit_type, self.build_helper)
        self.order.reserve()
        self.bot.producer.submit(self.order)

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

    async def start(self):
        await super().start()
        self.order = OrderUpgrade(self.upgrade_id)
        self.bot.producer.submit(self.order)

    async def execute(self) -> bool:
        return self.order.is_done    

    def debug_string(self) -> str:
        if self.order:
            return self.order.debug_string()
        else:
            return "$Upgrade-" +str(self.upgrade_id).replace("UpgradeId.", "")