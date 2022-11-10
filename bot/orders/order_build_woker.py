from typing import Union
from bot.orders.order_build import OrderBuild
from bot.orders.interface_build_helper import InterfaceBuildHelper
from bot.squads.squad_mining import SquadMining
from bot.bot_ai_base import BotAIBase
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit

class OrderBuildWorker(OrderBuild):
    def __init__(self, build_type : UnitTypeId, build_helper: InterfaceBuildHelper) -> None:
        super().__init__()
        self.build_type = build_type
        self.worker_tag = None
        self.build_helper = build_helper
        self.out_build: Unit = None

    def on_submit(self, bot: BotAI):
        super().on_submit(bot)

        self.worker_tag = None
        unit_data = self.bot.game_data.units[self.build_type.value]
        cost = self.bot.game_data.calculate_ability_cost(unit_data.creation_ability)

        self.cost_vespene = cost.vespene
        self.cost_minerals = cost.minerals

    @property
    def has_item(self) -> bool:
        return not self.worker_tag

    @property
    def is_producing(self) -> bool:
        return self.worker_tag

    async def produce(self):

        if self.build_type == UnitTypeId.REFINERY:
            geyser_tag = self.build_helper.get_vespene_geyser()
            if not geyser_tag:
                return False

            geyser = self.bot.vespene_geyser.find_by_tag(geyser_tag)
            worker = self.build_helper.get_worker(geyser.position)
            if not worker:
                return False

            worker.build_gas(geyser)
            self.worker_tag = worker.tag
            return True
        else:
            #todo 如果position失败了，就不要lock city
            position = await self.build_helper.get_build_position(self.build_type)
            if not position or not await self.bot.can_place(self.build_type, position):
                return False
            worker = self.build_helper.get_worker(position)
            if not worker:
                return False

            worker.build(self.build_type, position)
            self.worker_tag = worker.tag
            return True

        return False

    def on_building_construction_complete(self, unit: Unit):
        if unit.type_id != self.build_type or self.worker_tag is None:
            return False

        self.out_build = unit
        self.is_done = True
        self.build_helper.on_build_complete(unit, self.worker_tag)

        return True

    def debug_string(self) -> str:
        return "$Build-" + str(self.build_type).replace("UnitTypeId.", "") + self.debug_get_progress_char()

    def post_step(self):
        self.out_build = None
