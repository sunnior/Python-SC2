from typing import Union
from bot.orders.order_build import OrderBuild
from bot.squads.squad_mining import SquadMining
from bot.bot_ai_base import BotAIBase
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit

class OrderBuildWorker(OrderBuild):
    def __init__(self, build_type : UnitTypeId, target: Union[Point2, int]) -> None:
        super().__init__()
        self.build_type = build_type
        self.worker_tag = None
        self.target = target
        self.out_build: Unit = None

    def on_submit(self, bot: BotAI):
        super().on_submit(bot)

        unit_data = self.bot.game_data.units[self.build_type.value]
        cost = self.bot.game_data.calculate_ability_cost(unit_data.creation_ability)

        self.cost_vespene = cost.vespene
        self.cost_minerals = cost.minerals

    @property
    def has_item(self) -> bool:
        return self.worker_tag is None

    @property
    def is_producing(self) -> bool:
        return self.worker_tag is not None

    async def produce(self):
        if isinstance(self.target, Point2) and not await self.bot.can_place(self.build_type, self.target):
            return False

        for squad in self.bot.squads:
            if isinstance(squad, SquadMining):
                worker_tag = squad.remove_worker()
                break

        if worker_tag is None:
            return False

        self.worker_tag = worker_tag
        worker = self.bot.workers.find_by_tag(worker_tag)

        if self.build_type == UnitTypeId.REFINERY:
            worker.build_gas(self.bot.vespene_geyser.find_by_tag(self.target))
        else:
            worker.build(self.build_type, self.target)

        return True

    def on_building_construction_complete(self, unit: Unit):
        if unit.type_id != self.build_type or self.worker_tag is None:
            return False

        self.out_build = unit
        self.is_done = True
        for squad in self.bot.squads:
            if isinstance(squad, SquadMining):
                #todo 这个地方怎么处理worker的回收
                squad.add_worker(self.bot.units.find_by_tag(self.worker_tag))
                break

        return True

    def debug_string(self) -> str:
        return "$Build-" + str(self.build_type).replace("UnitTypeId.", "") + self.debug_get_progress_char()

    def post_step(self):
        self.out_build = None
