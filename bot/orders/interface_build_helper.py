from typing import Optional
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit


class InterfaceBuildHelper():
    def __init__():
        pass

    async def get_build_position(self, unit_type: UnitTypeId) -> Optional[Point2]:
        assert(False)

    async def get_vespene_geyser(self) -> Optional[int]:
        assert(False)

    def get_worker(self) -> Optional[Unit]:
        assert(False)
        
    def on_build_complete(self, unit: Unit, worker_tag: int):
        if worker_tag:
            assert(False)

    def on_addon_complete(self, unit: Unit):
        assert(False)
