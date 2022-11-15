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
        
        for arg in argv:
            assert(isinstance(arg, ActBase))   
            self.act_list_init.append(arg)

        assert(len(self.act_list_init) > 0)

    def on_added(self, bot: BotAI):
        super().on_added(bot)

        self.act_list = self.act_list_init.copy()

        for act in self.act_list:
            act.on_added(bot)

    async def execute(self) -> bool:
        self.act_list, act_list_tmp = [], self.act_list

        for act in act_list_tmp:
            if await act.execute():
                act.on_removed()
            else:
                self.act_list.append(act)

        return not len(self.act_list)

    def debug_string(self) -> str:
        use_list = self.act_list_init
        if self.is_added:
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


    def on_added(self, bot: BotAI):
        super().on_added(bot)

        self.act_list = self.act_list_init.copy()
        self.act_list[0].on_added(bot)

    async def execute(self) -> bool:
        if await self.act_list[0].execute():
            self.act_list[0].on_removed()
            self.act_list.pop(0)
            if len(self.act_list):
                self.act_list[0].on_added(self.bot)
            else:
                return True

        return False

    def debug_string(self) -> str:
        use_list = self.act_list_init
        if self.is_added:
            use_list = self.act_list

        debug_info = "Seq[["
        for act in use_list:
            debug_info = debug_info + " " + act.debug_string()

        debug_info = debug_info + "]]"
        return debug_info

class ActLoop(ActComposite):
    def __init__(self, act: ActBase, count: int = 999999):
        super().__init__()
    
        self.act = act
        self.count = count


    def on_added(self, bot: BotAI):
        super().on_added(bot)
        self.it_count = 0
        
        self.act.on_added(bot)

    async def execute(self) -> bool:
        if await self.act.execute():
            self.act.on_removed()
            self.it_count = self.it_count + 1
            if self.it_count == self.count:
                return True
            
            self.act.on_added(self.bot)

    def debug_string(self) -> str:
        debug_info = "Loop[[" + self.act.debug_string() + "]]"
        return debug_info

    