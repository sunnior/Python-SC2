from bot.orders.order import Order
from bot.orders.order_unit import OrderUnit
from bot.orders.order_build import OrderBuild
from bot.orders.order_upgrade import OrderUpgrade
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import Unit

class ProducerManager():
    def __init__(self, bot: BotAI) -> None:
        self.orders : list[Order] = []
        self.bot = bot

    def submit(self, order : Order):
        self.orders.append(order)
        order.on_submit(self.bot)

    def unsubmit(self, order: Order):
        self.orders.remove(order)
        order.on_unsubmit()
        
    async def step(self):
        for order in self.orders:
            await order.step()
            if order.is_done:
                order.on_unsubmit()

        self.orders = [order for order in self.orders if not order.is_done ]

        pending_orders = [order for order in self.orders if order.has_item ]
        reserved_orders = []
        unreserved_orders = []
        for order in self.orders:
            if order.has_item:
                if order.is_reserved:
                    reserved_orders.append(order)
                else:
                    unreserved_orders.append(order)

        reserved_minerals = 0
        reserved_vespene = 0
        reserved_supply = 0

        for order in reserved_orders:
            reserved_minerals = reserved_minerals + order.cost_minerals
            reserved_vespene = reserved_vespene + order.cost_vespene
            reserved_supply = reserved_supply + order.cost_supply
    
        cost_minerals_left = max(0, self.bot.minerals - reserved_minerals)
        cost_vespene_left = max(0, self.bot.vespene - reserved_vespene)
        cost_supply_left = max(0, self.bot.supply_left - reserved_supply)

        #优先生成预订的
        is_produced = False
        for order in reserved_orders:
            if order.cost_minerals <= self.bot.minerals and order.cost_supply <= self.bot.supply_left and order.cost_vespene <= self.bot.vespene:
                #一次只生产一个
                if await order.produce():
                    is_produced = True
                    break

        if not is_produced:
            for order in unreserved_orders:
                if order.cost_minerals <= cost_minerals_left and order.cost_vespene <= cost_vespene_left and order.cost_supply <= cost_supply_left:
                    #一次只生产一个
                    if await order.produce():
                        is_produced = True
                        break
        
    def post_step(self):
        for order in self.orders:
            order.post_step()

    def on_unit_created(self, unit : Unit):
        # 寻找这个单位是哪一个unit创建的
        for order in self.orders:
            if isinstance(order, OrderUnit) and order.on_unit_create(unit):
                return

    def on_building_construction_complete(self, unit: Unit):
        for order in self.orders:
            if isinstance(order, OrderBuild) and order.on_building_construction_complete(unit):
                return

    def on_unit_type_changed(self, unit: Unit, previous_type: UnitTypeId):
        for order in self.orders:
            if isinstance(order, OrderBuild) and order.on_unit_type_changed(unit, previous_type):
                return

    def on_upgrade_complete(self, upgrade: UpgradeId):
        for order in self.orders:
            if isinstance(order, OrderUpgrade) and order.on_upgrade_complete(upgrade):
                return