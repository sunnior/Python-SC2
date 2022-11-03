from bot.bot_ai_base import BotAIBase
from bot.strategies.strategy import Strategy
from bot.strategies.Terran.strategy_terran_army import StrategyTerranArmy
from bot.strategies.Terran.strategy_terran_mining import StrategyTerranMining
from bot.strategies.Terran.strategy_terran_supply import StrategyTerranSupply

class StrategyTerranRoot(Strategy):
    def __init__(self) -> None:
        super().__init__()

    def post_init(self, bot: BotAIBase):
        super().post_init(bot)

        self.add_sub_strategy(StrategyTerranMining())
        self.add_sub_strategy(StrategyTerranSupply())
        self.add_sub_strategy(StrategyTerranArmy())

    def start(self):
        super().start()

    def debug_string(self) -> str:
        return "TerranRoot"