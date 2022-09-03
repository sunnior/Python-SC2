from bot.bot_ai_base import BotAIBase
from bot.strategies.strategy import Strategy
from bot.strategies.Terran.strategy_terran_army import StrategyTerranArmy
from bot.strategies.Terran.strategy_terran_mining import StrategyTerranMining
from bot.strategies.Terran.strategy_terran_supply import StrategyTerranSupply

class StrategyTerranRoot(Strategy):
    def __init__(self, bot : BotAIBase) -> None:
        super().__init__(bot)
        self.add_sub_strategy(StrategyTerranMining(bot))
        self.add_sub_strategy(StrategyTerranSupply(bot))
        self.add_sub_strategy(StrategyTerranArmy(bot))

    def start(self):
        super().start()

    def debug_string(self) -> str:
        return "TerranRoot"