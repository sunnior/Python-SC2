from typing import Optional
from bot.acts.act_check_unit import ActCheckBuildReady, ActCheckSupplyUsed
from bot.acts.act_order import ActOrderBuild, ActOrderBuildAddon, ActOrderTerranUnit
from bot.acts.act_flow_control import ActSequence
from bot.orders.interface_build_helper import InterfaceBuildHelper
from bot.bot_ai_base import BotAIBase
from bot.strategies.strategy import Strategy
from sc2.ids.unit_typeid import UnitTypeId
from bot.squads.squad_mining import SquadMining
from sc2.position import Point2
from sc2.unit import Unit

class BuildHelperTerranMining(InterfaceBuildHelper):
    def __init__(self, bot: BotAIBase, squads_ming: list[SquadMining], owner):
        self.bot = bot
        self.squads_mining = squads_ming
        self.owner = owner

    async def get_build_position(self, unit_type: UnitTypeId) -> Optional[Point2]:
        if unit_type == UnitTypeId.COMMANDCENTER:
            return await self.bot.get_next_expansion()

        return None

    async def get_vespene_geyser(self) -> Optional[int]:
        for squad in self.squads_mining:
            vespene_tag = squad.get_free_vespene()
            if vespene_tag is not None:
                return vespene_tag
        return None

    def get_worker(self) -> Optional[Unit]:
        for squad in self.squads_mining:
            if isinstance(squad, SquadMining):
                worker_tag = squad.remove_worker()
                break

        if worker_tag:
            return self.bot.workers.find_by_tag(worker_tag)

        return None

    def on_building_construction_complete(self, unit: Unit):
        if unit.type_id == UnitTypeId.COMMANDCENTER:
            self.owner.create_squad_mining(unit)
    
class StrategyTerranMining(Strategy, InterfaceBuildHelper):
    def __init__(self) -> None:
        super().__init__()
        
    def post_init(self, bot: BotAIBase):
        super().post_init(bot)
        self.squads_mining: list[SquadMining] = []
        self.build_helper = BuildHelperTerranMining(self.bot, self.squads_mining, self)

        act_build_orders = [
            ActSequence(ActCheckSupplyUsed(15), ActOrderBuild(UnitTypeId.REFINERY, self.build_helper)),  
            ActSequence(ActCheckSupplyUsed(18), ActCheckBuildReady(UnitTypeId.BARRACKS), ActOrderBuildAddon(UnitTypeId.ORBITALCOMMAND, self.build_helper)), 
            ActSequence(ActCheckSupplyUsed(20), ActOrderBuild(UnitTypeId.COMMANDCENTER, self.build_helper)),
        ]
        self.add_acts(act_build_orders)

        self.act_order_worker = ActOrderTerranUnit(UnitTypeId.SCV, 999)
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

    def create_squad_mining(self, townhall: Unit):
        squad_mining = SquadMining(self.bot, townhall)
        self.squads_mining.append(squad_mining)
        self.submit_squad(squad_mining)

    def debug_string(self) -> str:
        return "TerranMining"