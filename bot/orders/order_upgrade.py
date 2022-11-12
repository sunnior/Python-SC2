from bot.orders.order import Order
from sc2.bot_ai import BotAI
from sc2.dicts.upgrade_researched_from import UPGRADE_RESEARCHED_FROM
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

class OrderUpgrade(Order):
    def __init__(self, upgrade_id: UpgradeId) -> None:
        super().__init__()
        self.upgrade_id = upgrade_id
        self.build_id: UnitTypeId = UPGRADE_RESEARCHED_FROM[upgrade_id]
        self.build_tag = None

    @property
    def has_requests(self) -> bool:
        return not self.build_tag

    @property
    def is_producing(self) -> bool:
        return self.build_tag
        
    def on_submit(self, bot: BotAI):
        super().on_submit(bot)

        cost = self.bot.game_data.upgrades[self.upgrade_id.value].cost

        self.cost_vespene = cost.vespene
        self.cost_minerals = cost.minerals

    def on_unsubmit(self):
        #todo cancel build progress
        pass

    async def produce(self) -> bool:
        for builder in self.bot.structures:
            if builder.type_id != self.build_id:
                continue

            if builder.build_progress != 1:
                continue
            
            if len(builder.orders):
                continue

            if builder.research(self.upgrade_id):
                self.build_tag = builder.tag
                return True

        return False

    def on_upgrade_complete(self, upgrade_id: UpgradeId) -> bool:
        if upgrade_id == self.upgrade_id:
            self.is_done = True
            return True

        return False

    def debug_string(self) -> str:
        return "$Upgrade-" + str(self.upgrade_id).replace("UpgradeId.", "") + self.debug_get_progress_char()