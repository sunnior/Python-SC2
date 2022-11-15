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

    def add_order(self, order : Order):
        self.orders.append(order)
        order.on_added(self.bot)

    def remove_order(self, order: Order):
        self.orders.remove(order)
        order.on_removed()
        
    async def step(self):
        for order in self.orders:
            await order.step()
            if order.is_done:
                order.on_removed()

        self.orders = [order for order in self.orders if not order.is_done ]
        orders_request = [ order for order in self.orders if order.has_requests ]

        orders_request.sort(key=lambda x: x.priority)

        minerals_left = self.bot.minerals
        vespene_left = self.bot.vespene
        supply_left = self.bot.supply_left

        is_produced = False
        for order in orders_request:
            if order.cost_minerals <= minerals_left and order.cost_supply <= supply_left and order.cost_vespene <= vespene_left:
                #一次只生产一个
                if await order.produce():
                    is_produced = True
                    break

            minerals_left = max(0, minerals_left - order.cost_minerals)
            vespene_left = max(0, vespene_left - order.cost_vespene)
            supply_left = max(0, supply_left - order.cost_supply)

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