from bot.acts.act_base import ActBase
from bot.acts.act_flow_control import ActComposite
from bot.squads.squad import Squad
from bot.bot_ai_base import BotAIBase
from sc2.position import Point2
from sc2.unit import Unit

class Strategy():
    def __init__(self, bot : BotAIBase) -> None:
        self.substrategies : list[Strategy] = []
        self.bot = bot
        self.squads : list[Squad] = []
        self.acts_pending: list[ActBase] = []
        self.acts_ending: list[ActBase] = []
        self.acts: list[ActBase] = []

    def start(self):
        for strategy in self.substrategies:
            strategy.start()

    def add_acts(self, acts: list[ActBase]):
        for act in acts:
            self.acts_pending.append(act)
            act.post_init(self.bot)

    async def step(self):
        pass

    async def _step(self):
        for act in self.acts_ending:
            await act.stop()
        
        self.acts_ending.clear()

        self.acts_tmp = self.acts.copy()
        self.acts.clear()

        for act in self.acts_tmp:
            if await act.execute():
                self.acts_ending.append(act)
            else:
                self.acts.append(act)

        for act in self.acts_pending:
            await act.start()
            self.acts.append(act)

        self.acts_pending.clear()

        await self.step()

        for strategy in self.substrategies:
            await strategy._step()

    def add_sub_strategy(self, strategy):
        self.substrategies.append(strategy)

    def submit_squad(self, squad):
        self.squads.append(squad)
        self.bot.squads.append(squad)
        squad.on_submit()

    def on_unit_created(self, unit: Unit):
        pass

    def _on_unit_created(self, unit: Unit):

        self.on_unit_created(unit)
        for strategy in self.substrategies:
            strategy._on_unit_created(unit)

    def on_building_construction_complete(self, unit):
        pass

    def _on_building_construction_complete(self, unit: Unit):
        self.on_building_construction_complete(unit)

        for squad in self.squads:
            squad.on_building_construction_complete(unit)
            
        for strategy in self.substrategies:
            strategy._on_building_construction_complete(unit)

    def debug(self, prefix : str) -> str:
        debug_info =  self.debug_string() + "\n"
        if len(self.acts) > 0:
            debug_info = debug_info + prefix + "   Lacts: "
            for act in self.acts:
                debug_info = debug_info + act.debug_string() + " "
                if isinstance(act, ActComposite):
                    debug_info = debug_info + "\n" + prefix + "          "

        debug_info = debug_info + "\n"

        if len(self.squads) > 0:
            debug_info = debug_info + prefix + "   L "
            for squad in self.squads:
                debug_info = debug_info + " " + squad.debug_string()
            debug_info = debug_info + "\n"

        next_prefix = prefix + "    "
        for strategy in self.substrategies:
            debug_info = debug_info + next_prefix + "L " + strategy.debug(next_prefix + "  ")

        return debug_info

    def debug_string() -> str:
        return ""
