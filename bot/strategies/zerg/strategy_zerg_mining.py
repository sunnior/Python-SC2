from bot.bot_ai_base import BotAIBase
from bot.producer_manager import ProducerManager
from bot.strategies.strategy import Strategy
from sc2.ids.unit_typeid import UnitTypeId
from bot.orders.order_zerg_unit import OrderZergUnit

class StrategyZergMining(Strategy):
    def __init__(self, bot : BotAIBase) -> None:
        super().__init__(bot)
        
    def start(self):
        super().start()

        self.order = OrderZergUnit(self.bot, UnitTypeId.DRONE, 999)
        self.bot.producer.add_order(self.order)

    def step(self):
        pass

    def debug_string(self) -> str:
        return "ZergWorkerMining"      