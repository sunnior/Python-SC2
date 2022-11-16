from typing import Callable
from bot.orders.order import Order
from sc2.bot_ai import BotAI
from sc2.dicts.upgrade_researched_from import UPGRADE_RESEARCHED_FROM
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

class OrderUpgrade(Order):
    def __init__(self, upgrade_id: UpgradeId, callback: Callable = None) -> None:
        super().__init__()
        self.upgrade_id = upgrade_id
        self.build_id: UnitTypeId = UPGRADE_RESEARCHED_FROM[upgrade_id]
        self.build_tag = None
        self.priority = Order.prio_highest
        self.callback = callback

    @property
    def has_requests(self) -> bool:
        return not self.build_tag

    @property
    def is_producing(self) -> bool:
        return self.build_tag
        
    def on_added(self, bot: BotAI):
        super().on_added(bot)

        cost = self.bot.game_data.upgrades[self.upgrade_id.value].cost

        self.cost_vespene = cost.vespene
        self.cost_minerals = cost.minerals

    def on_removed(self):
        #todo cancel build progress
        pass

    async def produce(self) -> bool:
        for builder in self.bot.structures:
            if (
                builder.type_id != self.build_id or
                not builder.is_ready or
                not builder.is_idle
            ):
                continue

            if builder.research(self.upgrade_id):
                self.build_tag = builder.tag
                return True

        return False

    def on_upgrade_complete(self, upgrade_id: UpgradeId) -> bool:
        if upgrade_id == self.upgrade_id:
            self.is_done = True
            if self.callback:
                self.callback()
            return True

        return False

    def debug_string(self) -> str:
        return "$Upgrade-" + str(self.upgrade_id).replace("UpgradeId.", "") + self.debug_get_progress_char()