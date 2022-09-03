from sc2.bot_ai import BotAI

class ActBase():
    def __init__(self):
        self.bot: BotAI = None
        self.is_start: bool = False

    def post_init(self, bot: BotAI):
        self.bot = bot

    async def start(self):
        assert(not self.is_start)
        self.is_start = True

    async def stop(self):
        assert(self.is_start)
        self.is_start = False

    async def execute(self) -> bool:
        return True

    def debug_string(self) -> str:
        return "unknown"
    