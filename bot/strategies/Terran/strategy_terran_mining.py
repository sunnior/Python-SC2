from typing import Optional
from bot.acts.act_check_unit import ActCheckBuildReady
from bot.acts.act_flow_control import ActLoop, ActSequence
from bot.acts.act_order import ActOrderTerranUnit
from bot.acts.act_skill import ActSkill, ActSkillCallMule
from bot.bot_ai_base import BotAIBase
from bot.squads.squad_command_center import SquadCommandCenter
from bot.strategies.strategy import Strategy
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from bot.squads.squad_mining import SquadMining
from sc2.position import Point2
from sc2.unit import Unit
    
class StrategyTerranMining(Strategy):
    def __init__(self, squad_cc: SquadCommandCenter) -> None:
        super().__init__()
        self.is_order_worker = None
        self.squads_mining: list[SquadMining] = []
        self.new_workers: list[Unit] = []
        self.squad_cc: SquadCommandCenter = squad_cc

    def post_init(self, bot: BotAIBase):
        super().post_init(bot)

        for townhall in self.bot.townhalls:
            self.create_squad_mining(townhall)

        self.squads_mining[0].init_workers(self.bot.workers)

        self.act_order_worker = ActOrderTerranUnit(UnitTypeId.SCV, 99, self.on_order_unit_created)
        self.add_acts([self.act_order_worker])
        self.add_acts([ActSequence(ActCheckBuildReady(UnitTypeId.ORBITALCOMMAND), ActLoop(ActSkillCallMule(self.squad_cc, self.squads_mining)))]) 

    def step_new_worker(self):
        for worker in self.new_workers:
            self.add_worker(worker)

        self.new_workers.clear()

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

        if squad_under_saturate and squad_over_saturate:
            squad_under_saturate.add_unit(squad_over_saturate.get_worker())

    async def step(self):
        self.step_new_worker()
        self.step_balance_worker()

        saturation_left = 0
        for squad in self.squads_mining:
            saturation_left = saturation_left + squad.get_saturation_left()

        #留几个作为builder
        saturation_left = max(0, saturation_left + 2)
        self.act_order_worker.update_count(saturation_left)

        if saturation_left > 0 and not self.act_order_worker.is_added:
            self.add_acts([self.act_order_worker])

    def create_squad_mining(self, townhall: Unit):
        squad_mining = SquadMining(townhall)
        self.squads_mining.append(squad_mining)
        self.add_squad(squad_mining)

    def add_worker(self, worker: Unit):
        squads = self.squads_mining.copy()
        squads.sort(key=lambda squad: squad.position.distance_to(worker.position))
        for squad in squads:
            if squad.get_saturation_left() > 0:
                squad.add_unit(worker)
                worker = None
                break
        
        if worker:
            squads[0].add_unit(worker)

    def add_worker_tag(self, worker_tag: int):
        worker = self.bot.workers.find_by_tag(worker_tag)
        self.add_worker(worker)

    def remove_worker(self, near: Point2):
        squads = self.squads_mining.copy()
        squads.sort(key=lambda squad: squad.position.distance_to(near))
        worker = None
        for squad in squads:
            worker = squad.get_worker(near)
            if worker:
                return worker

    def get_vespene_geyser(self) -> Optional[int]:
        for squad in self.squads_mining:
            vespene_tag = squad.get_free_vespene()
            if vespene_tag is not None:
                return vespene_tag
        return None

    def on_order_unit_created(self, unit: Unit):
        self.new_workers.append(unit)

    def debug_string(self) -> str:
        return "TerranMining"