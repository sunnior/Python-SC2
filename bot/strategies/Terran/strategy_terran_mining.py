from typing import Optional
from bot.acts.act_order import ActOrderTerranUnit
from bot.orders.interface_build_helper import InterfaceBuildHelper
from bot.bot_ai_base import BotAIBase
from bot.strategies.strategy import Strategy
from sc2.ids.unit_typeid import UnitTypeId
from bot.squads.squad_mining import SquadMining
from sc2.position import Point2
from sc2.unit import Unit
    
class StrategyTerranMining(Strategy, InterfaceBuildHelper):
    def __init__(self) -> None:
        super().__init__()
        
    def post_init(self, bot: BotAIBase):
        super().post_init(bot)
        self.squads_mining: list[SquadMining] = []
        
        self.act_order_worker = ActOrderTerranUnit(UnitTypeId.SCV, 999)
        self.is_order_worker = True
        self.add_acts([self.act_order_worker])

    def start(self):
        super().start()

        for townhall in self.bot.townhalls:
            self.create_squad_mining(townhall)

        self.squads_mining[0].init_workers(self.bot.workers)

    def step_new_worker(self):
        for worker in self.act_order_worker.out_units:
            is_assigned = False
            for squad in self.squads_mining:
                if squad.get_saturation_left() > 0:
                    squad.add_worker(worker)
                    is_assigned = True
                    break
            if not is_assigned:
                self.squads_mining[0].add_worker(worker)

    def step_balance_worker(self):
        squad_over_saturate = None
        squad_under_saturate = None
        for squad in self.squads_mining:
            if squad.get_saturation_left() < 0:
                squad_over_saturate = squad
                break

        for squad in self.squads_mining:
            if squad.get_saturation_left() > 0:
                squad_under_saturate = squad
                break

        if squad_under_saturate is not None and squad_over_saturate is not None:
            worker_tag = squad_over_saturate.remove_worker()
            squad_under_saturate.add_worker(self.bot.units.find_by_tag(worker_tag))

    async def step(self):
        self.step_new_worker()
        self.step_balance_worker()

        saturation_left = 0
        for squad in self.squads_mining:
            saturation_left = saturation_left + squad.get_saturation_left()

        #留几个作为builder
        if saturation_left < -2:
            if self.is_order_worker:
                self.remove_acts(self.act_order_worker)
                self.is_order_worker = False
        else:
            if not self.is_order_worker:
                self.add_acts([self.act_order_worker])
                self.is_order_worker = True

    def create_squad_mining(self, townhall: Unit):
        squad_mining = SquadMining(self.bot, townhall)
        self.squads_mining.append(squad_mining)
        self.add_squad(squad_mining)

    def add_worker(self, worker_tag: int):
        self.squads_mining[0].add_worker(self.bot.workers.find_by_tag(worker_tag))

    def remove_worker(self, near: Point2):
        return self.bot.workers.find_by_tag(self.squads_mining[0].remove_worker())

    def get_vespene_geyser(self) -> Optional[int]:
        for squad in self.squads_mining:
            vespene_tag = squad.get_free_vespene()
            if vespene_tag is not None:
                return vespene_tag
        return None        

    def debug_string(self) -> str:
        return "TerranMining"