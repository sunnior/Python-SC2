import os
from bot.city.city import City
from bot.producer_manager import ProducerManager
from MapAnalyzer.MapData import MapData
from sc2.bot_ai import BotAI
from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import Unit
from cmap import init as cext_map_init

class BotAIBase(BotAI):

    def __init__(self) -> None:
        super().__init__()
        self.producer = ProducerManager(self)
        self.strategy = None
        self.race: Race = None
        self.locked_build_types: list[UnitTypeId] = []
        self.cities: list[City] = []

    def terrain_to_z_height(self, h):
        """Gets correct z from versions 4.9.0+"""
        return -16 + 32 * h / 255

    async def on_start(self):
        pid = os.getpid()
        print(pid)

        self.map_data : MapData = MapData(self)
        #self.map_data.plot_map()
        #self.map_data.save("xxxeeesss")

        region = self.map_data.where_all(self.start_location)[0]
        if self.race == Race.Terran:
            self.cities.append(City(self, self.map_data, region))

    async def on_step(self, iteration: int):

        str_test = cext_map_init()
        print(str_test)

        await self.producer.step()

        await self.strategy._step()

        if len(self.state.action_errors):
            print("***********************************error*******************************\n", self.state.action_errors)

        debug_str = self.strategy.debug("")
        self.client.debug_text_screen(debug_str, (0, 0), (0, 255, 0), 12)

        for city in self.cities:
            city.debug()

    def get_main_city(self) -> City:
        return self.cities[0]

    def add_strategy(self, strategy):
        self.strategy = strategy
        self.strategy.post_init(self)

    async def on_unit_created(self, unit: Unit):
        self.producer.on_unit_created(unit)
        self.strategy._on_unit_created(unit)

    async def on_upgrade_complete(self, upgrade: UpgradeId):
        self.producer.on_upgrade_complete(upgrade)

    async def on_building_construction_complete(self, unit: Unit):
        self.producer.on_building_construction_complete(unit)
        for city in self.cities:
            city.on_building_complete(unit)

        self.strategy._on_building_construction_complete(unit)

    async def on_unit_type_changed(self, unit: Unit, previous_type: UnitTypeId):
        self.producer.on_unit_type_changed(unit, previous_type)

    async def on_unit_destroyed(self, unit_tag: int):
        unit = self._all_units_previous_map[unit_tag]
        self.strategy._on_unit_destroyed(unit)

