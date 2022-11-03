from typing import Optional
from bot.acts.act_check_unit import ActCheckBuildReady, ActCheckSupplyUsed
from bot.acts.act_order import ActOrderBuild, ActOrderBuildAddon, ActOrderBuildGas, ActOrderTerranUnit
from bot.acts.act_flow_control import ActSequence
from bot.acts.interface_build_helper import InterfaceBuildHelper
from bot.bot_ai_base import BotAIBase
from bot.strategies.strategy import Strategy
from sc2.ids.unit_typeid import UnitTypeId
from bot.squads.squad_mining import SquadMining
from sc2.position import Point2
from sc2.unit import Unit

class StrategyTerranMining(Strategy, InterfaceBuildHelper):
    def __init__(self) -> None:
        super().__init__()
        self.squads_mining: list[SquadMining] = []
        
    def post_init(self, bot: BotAIBase):
        super().post_init(bot)
        
        act_build_orders = [
            ActSequence(ActCheckSupplyUsed(15), ActOrderBuildGas(self)),  
            ActSequence(ActCheckSupplyUsed(18), ActCheckBuildReady(UnitTypeId.BARRACKS), ActOrderBuildAddon(UnitTypeId.ORBITALCOMMAND)), 
            ActSequence(ActCheckSupplyUsed(20), ActOrderBuild(UnitTypeId.COMMANDCENTER, self)),
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

    async def get_build_location(self, unit_type: UnitTypeId) -> Optional[Point2]:
        if unit_type == UnitTypeId.COMMANDCENTER:
            return await self.bot.get_next_expansion()

        return None

    def get_vespene_geyser(self) -> Optional[int]:
        for squad in self.squads_mining:
            vespene_tag = squad.get_free_vespene()
            if vespene_tag is not None:
                return vespene_tag
        return None

    def on_building_construction_complete(self, unit: Unit):
        if unit.type_id == UnitTypeId.COMMANDCENTER:
            self.create_squad_mining(unit)


    def create_squad_mining(self, townhall: Unit):
        squad_mining = SquadMining(self.bot, townhall)
        self.squads_mining.append(squad_mining)
        self.submit_squad(squad_mining)

    def debug_string(self) -> str:
        return "TerranMining"