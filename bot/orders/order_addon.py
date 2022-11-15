from typing import Callable
from bot.bot_ai_base import BotAIBase
from bot.orders.order_build import OrderBuild
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit
from bot.orders.interface_build_helper import InterfaceBuildHelper

class OrderAddon(OrderBuild):
 
    def __init__(self, unit_type: UnitTypeId, build_helper: InterfaceBuildHelper, callback: Callable = None):
        super().__init__()

        self.target_type = unit_type
        self.builder_helper = build_helper
        self.callback = callback

        self.from_type = None
        self.out_build = None
        #todo
        if unit_type == UnitTypeId.ORBITALCOMMAND:
            self.from_type = UnitTypeId.COMMANDCENTER
        elif unit_type == UnitTypeId.BARRACKSREACTOR or unit_type == UnitTypeId.BARRACKSTECHLAB:
            self.from_type = UnitTypeId.BARRACKS
        elif unit_type == UnitTypeId.FACTORYTECHLAB or unit_type == UnitTypeId.FACTORYREACTOR:
            self.from_type = UnitTypeId.FACTORY
        elif unit_type == UnitTypeId.STARPORTREACTOR or unit_type == UnitTypeId.STARPORTTECHLAB:
            self.from_type = UnitTypeId.STARPORT
        else:
            assert(False)

        self.builder_tag = None

    def on_added(self, bot: BotAI):
        super().on_added(bot)

        self.builder_tag = None
        unit_data = self.bot.game_data.units[self.target_type.value]
        cost = self.bot.game_data.calculate_ability_cost(unit_data.creation_ability)

        self.cost_vespene = cost.vespene
        self.cost_minerals = cost.minerals
    
    @property
    def has_requests(self) -> bool:
        return self.builder_tag is None

    @property
    def is_producing(self) -> bool:
        return self.builder_tag is not None

    async def produce(self):
        for builder in self.bot.structures:
            if builder.type_id == self.from_type and not builder.has_add_on:
                if builder.build_progress == 1 and len(builder.orders) == 0:
                    if builder.train(self.target_type):
                        self.builder_tag = builder.tag
                        return True
    
    def on_unit_type_changed(self, unit: Unit, previous_type: UnitTypeId):
        #有的类型是typechange比如orbitalcommand，有的不是比如xxxtechlab
        if unit.type_id == self.target_type:
            self.is_done = True
            self.out_build = unit
            self.builder_helper.on_addon_complete(unit)
            return True

    def on_building_construction_complete(self, unit: Unit):
        if unit.type_id == self.target_type:
            self.is_done = True
            if self.callback:
                self.callback(unit)

            self.builder_helper.on_addon_complete(unit)
            return True

    def debug_string(self) -> str:
        return "$AddOn-" + str(self.target_type).replace("UnitTypeId.", "") + self.debug_get_progress_char()

    