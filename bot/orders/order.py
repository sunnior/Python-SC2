"""
需要消耗资源的操作，比如生成单位，建造，升级单位资源，科技点，附属建筑，这些操作都需要考虑优先级，有竞争关系
"""
from turtle import st
from sc2.bot_ai import BotAI
from sc2.unit import Unit


class Order():
    def __init__(self) -> None:
        self.is_done = False
        self.cost_minerals = 0
        self.cost_vespene = 0
        self.cost_supply = 0
        self.debug_progress_char = "\\"

        self.is_reserved = False

        self.priority = 0

    def on_submit(self, bot: BotAI):
        self.bot = bot

    def on_unsubmit(self):
        pass

    @property
    def has_item(self) -> bool:
        return False

    @property
    def is_producing(self) -> bool:
        return False

    async def step(self):
        pass

    def reserve(self):
        self.is_reserved = True

    async def produce(self) -> bool:
        return False

    def post_step(self):
        pass

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

    
