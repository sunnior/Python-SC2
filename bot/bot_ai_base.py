import os
from bot.city.city import City
from bot.producer_manager import ProducerManager
from sc2.bot_ai import BotAI
from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import Unit
from bot.map.map_tool import MapTool
from cmap_tool import init as cmap_tool_init

class BotAIBase(BotAI):

    def __init__(self) -> None:
        super().__init__()
        self.producer = ProducerManager(self)
        self.strategy = None
        self.race: Race = None
        self.locked_build_types: list[UnitTypeId] = []
        self.cities: list[City] = []

    async def on_start(self):
        #pid = os.getpid()
        #print(pid)

        self.map_tool = MapTool(self)
        #MapTool.test_cpp()
        #self.map_tool.debug()
        #City(self, self.map_tool.get_region(self.start_location))

        city = City(self, self.map_tool, self.map_tool.get_region(self.start_location))
        self.cities.append(city)

    async def on_step(self, iteration: int):
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

