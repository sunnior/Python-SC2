from bot.acts.act_base import ActBase
from sc2.ids.unit_typeid import UnitTypeId

class ActCheckSupplyUsed(ActBase):
    def __init__(self, count: int):
        super().__init__()
        self.count = count

    async def execute(self) -> bool:
        return self.bot.supply_used >= self.count

    def debug_string(self) -> str:
        return "?Supply>=" + str(self.count)

class ActCheckBuildReady(ActBase):
    def __init__(self, *argv):
        super().__init__()
        self.unit_types: list[UnitTypeId] = []
        for arg in argv:
            assert(isinstance(arg, UnitTypeId))
            self.unit_types.append(arg)

    async def execute(self) -> bool:
        for structure in self.bot.structures:
            if structure.type_id in self.unit_types:
                if structure.build_progress == 1:
                    return True

        return False

    def debug_string(self) -> str:
        return "?Ready" + str(self.unit_types).replace("UnitTypeId.", "")
