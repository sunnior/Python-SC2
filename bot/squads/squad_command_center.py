from bot.squads.squad import Squad
from sc2.unit import Unit
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId

class SquadCommandCenter(Squad):
    def __init__(self) -> None:
        super().__init__()
        #todo 放到一个统一的地方
        self.cost_energy_mule = 50

    def get_cc_for_mule(self) -> Unit:
        for cc in self.bot.townhalls(UnitTypeId.ORBITALCOMMAND).ready:
            if cc.energy >= self.cost_energy_mule:
                return cc