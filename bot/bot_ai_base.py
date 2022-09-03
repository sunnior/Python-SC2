from distutils.command.build import build
from MapAnalyzer.MapData import MapData
from bot.squads.squad import Squad
from sc2.bot_ai import BotAI
from bot.producer_manager import ProducerManager
from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point3
from sc2.unit import Unit

class BotAIBase(BotAI):

    def __init__(self) -> None:
        super().__init__()
        self.producer = ProducerManager(self)
        self.strategy = None
        self.squads: list[Squad] = []
        self.race: Race = None
        self.locked_build_types: list[UnitTypeId] = []

    def terrain_to_z_height(self, h):
        """Gets correct z from versions 4.9.0+"""
        return -16 + 32 * h / 255

    async def on_start(self):
        self.map_data : MapData = MapData(self)

    async def on_step(self, iteration: int):
        await self.producer.step()
        for squad in self.squads:
            squad.step()
            
        await self.strategy._step()

        self.producer.post_step()

        debug_str = self.strategy.debug("")
        self.client.debug_text_screen(debug_str, (0, 0), (0, 255, 0), 12)


        base_location = self.townhalls[0].position
        region = self.map_data.where_all(base_location)[0]
        choke_area = region.region_chokes[0]
        buildables = choke_area.buildables
        in_color = (0, 255, 0)
        """
        terrain_height = self.map_data.terrain_height.copy().T

        show_points = []
        for point in buildables.points:
            in_point = Point3((*point, self.terrain_to_z_height(terrain_height[point])))
            show_points.append(in_point)
            self.client.debug_box2_out(in_point, color=in_color, half_vertex_length=0.25)
        """

    async def on_unit_created(self, unit: Unit):
        self.producer.on_unit_created(unit)
        self.strategy._on_unit_created(unit)

    async def on_building_construction_complete(self, unit: Unit):
        self.producer.on_building_construction_complete(unit)
        self.strategy._on_building_construction_complete(unit)

    async def on_unit_type_changed(self, unit: Unit, previous_type: UnitTypeId):
        self.producer.on_unit_type_changed(unit, previous_type)

    async def on_unit_destroyed(self, unit_tag: int):
        pass

