from bot.squads.squad import Squad
from sc2.unit import Unit
from sc2.bot_ai import BotAI


class SquadScout(Squad):
    def __init__(self) -> None:
        super().__init__()
        self.unit_tag = None
        self.unit_type = None


    def on_added(self, bot: BotAI):
        super().on_added(bot)


    def add_unit(self, unit: Unit):
        super().add_unit(unit)
        self.unit_tag = unit.tag
        self.unit_type = unit.type_id

        unit.move(self.bot.enemy_start_locations[0])

    def on_my_unit_destroyed(self, unit: Unit):
        self.unit_tag = None

    def debug_string(self) -> str:
        if not self.unit_tag:
            return "Scout-None"

        return "Scout-" + str(self.unit_type).replace("UnitTypeId.", "") 