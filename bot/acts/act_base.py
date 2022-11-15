from sc2.bot_ai import BotAI

class ActBase():
    def __init__(self):
        self.bot: BotAI = None
        self.is_added = False

    def on_added(self, bot: BotAI):
        self.bot = bot
        assert(not self.is_added)
        self.is_added = True

    def on_removed(self):
        assert(self.is_added)
        self.is_added = False

    async def execute(self) -> bool:
        return True

    def debug_string(self) -> str:
        return "unknown"
    