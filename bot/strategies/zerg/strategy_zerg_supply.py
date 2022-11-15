from bot.bot_ai_base import BotAIBase
from bot.producer_manager import ProducerManager
from bot.strategies.strategy import Strategy
from sc2.ids.unit_typeid import UnitTypeId
from bot.orders.order_zerg_unit import OrderZergUnit

class StrategyZergSupply(Strategy):
    def __init__(self, bot : BotAIBase) -> None:
        super().__init__(bot)
        self.order = None
    
    def step(self):
        if self.bot.supply_left < 1 and self.order == None :
            self.order = OrderZergUnit(self.bot, UnitTypeId.OVERLORD, 1)
            self.bot.producer.add_order(self.order)
            
        if self.order:
            if self.order.is_done:
                self.order = None

    def debug_string(self) -> str:
        return "ZergSupply"                