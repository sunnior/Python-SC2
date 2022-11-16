from bot.acts.act_base import ActBase
from bot.squads.squad_command_center import SquadCommandCenter
from bot.squads.squad_mining import SquadMining
from sc2.ids.ability_id import AbilityId


class ActSkill(ActBase):
    def __init__(self) -> None:
        super().__init__()


class ActSkillCallMule(ActSkill):
    def __init__(self, squad_cc: SquadCommandCenter, squads_mining: list[SquadMining]) -> None:
        super().__init__()
        self.squad_cc: SquadCommandCenter = squad_cc
        self.squads_mining: list[SquadMining] = squads_mining

    async def execute(self) -> bool:
        cc = self.squad_cc.get_cc_for_mule()
        if not cc:
            return False

        for squad_mining in self.squads_mining:
            if squad_mining.get_saturation_left() <= 0:
                continue

            mineral = self.bot.mineral_field.find_by_tag(squad_mining.get_random_mineral_field())
            if cc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, mineral):
                return True
        
        return False

    def debug_string(self) -> str:
        return "CallMule"
