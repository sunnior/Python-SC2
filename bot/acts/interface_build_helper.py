from typing import Optional
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit


class InterfaceBuildHelper():
    def __init__():
        pass

    async def get_build_location(self, unit_type: UnitTypeId) -> Optional[Point2]:
        return None

    async def get_vespene_geyser(self) -> Optional[int]:
        return None

    def on_build_complete(self, unit: Unit):
        pass