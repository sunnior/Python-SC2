"""
需要消耗资源的操作，比如生成单位，建造，升级单位资源，科技点，附属建筑，这些操作都需要考虑优先级，有竞争关系
"""
from turtle import st
from sc2.bot_ai import BotAI
from sc2.unit import Unit


class Order():
    prio_highest = 0
    prio_high = 1
    prio_medium = 2
    prio_low = 3

    def __init__(self) -> None:
        self.is_done = False
        self.cost_minerals = 0
        self.cost_vespene = 0
        self.cost_supply = 0
        self.debug_progress_char = "\\"

        self.priority = Order.prio_low

    def on_added(self, bot: BotAI):
        self.bot = bot

    def on_removed(self):
        pass

    @property
    def has_requests(self) -> bool:
        assert(False)

    @property
    def is_producing(self) -> bool:
        assert(False)

    async def step(self):
        pass

    async def produce(self) -> bool:
        return False

    def debug_string(self) -> str:
        return "order"

    def debug_get_progress_char(self) -> str:
        if not self.is_producing:
            return "-"

        if self.debug_progress_char == "-":
            self.debug_progress_char = "\\"
        elif self.debug_progress_char == "\\":
            self.debug_progress_char = "/"
        elif self.debug_progress_char == "/":
            self.debug_progress_char = "-"

        return self.debug_progress_char

    
