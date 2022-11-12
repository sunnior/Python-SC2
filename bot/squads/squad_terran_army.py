from bot.squads.squad import Squad
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit

class SquadTerranArmy(Squad):
    def __init__(self, compositions: list[tuple[UnitTypeId, float]]) -> None:
        super().__init__()
        self.compositions: list[tuple[UnitTypeId, float, list[int]]] = []
        for composition in compositions:
            self.compositions.append((composition[0], composition[1], []))
        self.cache_count_total = 0

    def add_unit(self, unit: Unit):
        for composition in self.compositions:
            if composition[0] == unit.type_id:
                composition[2].append(unit.tag)
                self.cache_count_total = self.cache_count_total + 1
                return

        assert(False)

    def is_short_of(self, unit_type: UnitTypeId):
        for composition in self.compositions:
            if composition[0] == unit_type:
                return float(len(composition[2])) / self.cache_count_total < composition[1]

        return False

    def debug_string(self) -> str:
        debug_info = "TerranArm-" 
        for composition in self.compositions:
            debug_info = debug_info + str(composition[0]).replace("UnitTypeId.", "") + "-" + str(len(composition[2])) + " "
        return debug_info