from bot.bot_ai_base import BotAIBase
from bot.strategies.strategy import Strategy
from bot.strategies.Terran.strategy_terran_pig_start import StrategyTerranPigStart

class StrategyTerranRoot(Strategy):
    def __init__(self) -> None:
        super().__init__()

    def post_init(self, bot: BotAIBase):
        super().post_init(bot)

        self.add_sub_strategy(StrategyTerranPigStart())

    def debug_string(self) -> str:
        return "TerranRoot"