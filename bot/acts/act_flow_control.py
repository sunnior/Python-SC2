from distutils.log import debug
from faulthandler import is_enabled
from bot.acts.act_base import ActBase
from sc2.bot_ai import BotAI

class ActComposite(ActBase):
    def __init__(self):
        super().__init__()

class ActAnd(ActBase):
    def __init__(self, *argv):
        super().__init__()

        self.act_list_init: list[ActBase] = []
        self.act_list: list[ActBase] = []
        self.act_ending: list[ActBase] = []
        
        for arg in argv:
            assert(isinstance(arg, ActBase))   
            self.act_list_init.append(arg)

        assert(len(self.act_list_init) > 0)

    def post_init(self, bot: BotAI):
        super().post_init(bot)

        for act in self.act_list_init:
            act.post_init(bot)

    async def start(self):
        await super().start()
        self.act_list = self.act_list_init.copy()
        for act in self.act_list:
            await act.start()

    async def execute(self) -> bool:
        for act in self.act_ending:
            await act.stop()
        self.act_ending.clear()
        if len(self.act_list) == 0:
            return True

        act_list_tmp = self.act_list.copy()
        self.act_list.clear()

        for act in act_list_tmp:
            if await act.execute():
                self.act_ending.append(act)
            else:
                self.act_list.append(act)

        return False

    def debug_string(self) -> str:
        use_list = self.act_list_init
        if self.is_start:
            use_list = self.act_list
        debug_info = "And[["
        for act in use_list:
            debug_info = debug_info + act.debug_string() + " "
        
        debug_info = debug_info + "]]"
        return debug_info

class ActSequence(ActComposite):
    def __init__(self, *argv):
        super().__init__()

        self.act_list_init: list[ActBase] = []
        self.act_list: list[ActBase] = []
        self.act_ending: ActBase = None

        for arg in argv:
            assert(isinstance(arg, ActBase))   
            self.act_list_init.append(arg)

        assert(len(self.act_list_init) > 0)


    def post_init(self, bot: BotAI):
        super().post_init(bot)

        for act in self.act_list_init:
            act.post_init(bot)

    async def start(self):
        await super().start()
        self.act_list = self.act_list_init.copy()
        self.act_ending = None
        await self.act_list[0].start()

    async def execute(self) -> bool:
        if self.act_ending:
            await self.act_ending.stop()
            self.act_ending = None
            if len(self.act_list) > 0:
                await self.act_list[0].start()
                return False
            else:
                return True

        if await self.act_list[0].execute():
            self.act_ending = self.act_list.pop(0)

        return False

    def debug_string(self) -> str:
        debug_info = "Seq[["
        for act in self.act_list[:4]:
            debug_info = debug_info + " " + act.debug_string()
        if len(self.act_list) > 4:
            debug_info = debug_info + " ..."

        debug_info = debug_info + "]]"
        return debug_info

class ActLoop(ActComposite):
    def __init__(self, act: ActBase, count: int = 999999):
        super().__init__()
    
        self.act = act
        self.count = count


    def post_init(self, bot: BotAI):
        super().post_init(bot)
        self.act.post_init(bot)

    async def start(self):
        await super().start()
        self.it_count = 0
        self.it_end = False
        self.it_start = False
        await self.act.start()

    async def execute(self) -> bool:
        if self.it_end:
            self.it_end = False
            await self.act.stop()
            self.it_count = self.it_count + 1
            if self.it_count >= self.count:
                return True
            else:
                self.it_start = True
                return False
        elif self.it_start:
            self.it_start = False
            await self.act.start()
        else:
            if await self.act.execute():
                self.it_end = True
            return False

    def debug_string(self) -> str:
        debug_info = "Loop[[" + self.act.debug_string() + "]]"
        return debug_info

    