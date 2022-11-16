from typing import Union
from bot.squads.squad import Squad
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit

class SquadTerranArmy(Squad):
    def __init__(self, compositions: list[tuple[UnitTypeId, int]]) -> None:
        super().__init__()
        self.compositions: list[dict] = []

        sum_target_count = sum([ composition[1] for composition in compositions ])
        for composition in compositions:
            self.compositions.append({"type" : composition[0], "max" : composition[1], "percent" : float(composition[1]) / sum_target_count, "units" : []})
        self.cache_count_total = 0

    def add_unit(self, unit: Unit):
        for composition in self.compositions:
            if composition["type"] == unit.type_id:
                composition["units"].append(unit.tag)
                self.cache_count_total = self.cache_count_total + 1
                return

        assert(False)

    def on_unit_destroyed(self, unit: Unit):
        for composition in self.compositions:
            if composition["type"] == unit.type_id and unit.tag in composition["units"]:
                composition["units"].remove(unit.tag)
                return        

    def attack(self, target: Union[Point2, Unit]):
        for composition in self.compositions:
            for unit_tag in composition["units"]:
                unit = self.bot.units.find_by_tag(unit_tag)
                unit.attack(target)
                
    def is_short_of(self, unit_type: UnitTypeId):
        for composition in self.compositions:
            if composition["type"] == unit_type:
                return float(len(composition["units"])) / self.cache_count_total < composition["percent"]

        return False

    def is_overloaded(self):
        for composition in self.compositions:
            if composition["max"] > len(composition["units"]):
                return False

        return True

    def debug_string(self) -> str:
        debug_info = "TerranArm-" 
        for composition in self.compositions:
            debug_info = debug_info + str(composition["type"]).replace("UnitTypeId.", "") + "-" + str(len(composition["units"])) + " "
        return debug_info