from bot.bot_ai_base import BotAIBase
from bot.producer_manager import ProducerManager
from bot.strategies.strategy import Strategy
from bot.strategies.zerg import StrategyZergSupply
from bot.strategies.zerg import StrategyZergMining

class StrategyZergRoot(Strategy):
    def __init__(self, bot : BotAIBase) -> None:
        super().__init__(bot,)
        self.add_sub_strategy(StrategyZergMining(bot))
        self.add_sub_strategy(StrategyZergSupply(bot))

    def start(self):
        super().start()

    def debug_string(self) -> str:
        return "ZergRoot"