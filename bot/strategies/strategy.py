from bot.acts.act_base import ActBase
from bot.acts.act_flow_control import ActComposite
from bot.squads.squad import Squad
from bot.bot_ai_base import BotAIBase
from sc2.unit import Unit

class Strategy():
    def __init__(self) -> None:
        self.substrategies : list[Strategy] = []
        self.squads : list[Squad] = []
        self.acts: list[ActBase] = []

    def post_init(self, bot : BotAIBase):
        self.bot = bot

    def start(self):
        for strategy in self.substrategies:
            strategy.start()

    def add_acts(self, acts: list[ActBase]):
        for act in acts:
            if act in self.acts:
                continue

            assert(not act.is_added)
            self.acts.append(act)
            act.on_added(self.bot)

    def remove_acts(self, act: ActBase):
        assert(act.is_added and act in self.acts)
        self.acts.remove(act)
        act.on_removed()

    async def step(self):
        pass

    async def _step(self):

        acts_tmp, self.acts = self.acts, []

        for act in acts_tmp:
            if await act.execute():
                act.on_removed()
            else:
                self.acts.append(act)

        await self.step()

        for squad in self.squads:
            squad.step()
            

        for strategy in self.substrategies:
            await strategy._step()

    def add_sub_strategy(self, strategy):
        strategy.post_init(self.bot)
        self.substrategies.append(strategy)

    def add_squad(self, squad):
        self.squads.append(squad)
        squad.on_added(self.bot)

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

    def _on_unit_destroyed(self, unit: Unit):
        for squad in self.squads:
            squad.on_unit_destroyed(unit)

        self.on_unit_destroyed(unit)
        for strategy in self.substrategies:
            strategy._on_unit_destroyed(unit)

    def on_unit_destroyed(self, unit: int):
        pass

    def debug(self, prefix : str) -> str:
        debug_info =  self.debug_string() + "\n"
        if len(self.acts) > 0:
            debug_info = debug_info + prefix + "   Lacts: "
            for act in self.acts:
                debug_info = debug_info + act.debug_string() + " "
                #if isinstance(act, ActComposite):
                debug_info = debug_info + "\n" + prefix + "          "

        debug_info = debug_info + "\n"

        if len(self.squads) > 0:
            debug_info = debug_info + prefix + "   L "
            for squad in self.squads:
                debug_info = debug_info + " " + squad.debug_string() + "\n" + prefix + "     "
            debug_info = debug_info + "\n"

        next_prefix = prefix + "  "
        for strategy in self.substrategies:
            debug_info = debug_info + next_prefix + "L " + strategy.debug(next_prefix + "  ")
            debug_info = debug_info + "\n"

        return debug_info

    def debug_string(self) -> str:
        return ""
