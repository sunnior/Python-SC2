
import random
from bot.bot_ai_base import BotAIBase
from bot.squads.squad import Squad
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit

class SquadMining(Squad):

    def __init__(self, townhall: Unit) -> None:
        super().__init__()
        self.workers_mineral: list[int] = []
        self.workers_vespene: list[tuple[int, list[int]]] = []
        self.townhall = townhall.tag
        self.position = townhall.position

    def on_added(self, bot: BotAI):
        super().on_added(bot)
        expansion_locations_dict = bot.expansion_locations_dict
        resource_list = expansion_locations_dict[self.position]
        
        self.mineral_field = [ mineral.tag for mineral in resource_list.mineral_field ]
        self.vespene_geyser = [ vespene.tag for vespene in resource_list.vespene_geyser ]

    def step(self):
        #todo 默认采气
        if len(self.workers_mineral) > 0:
            for workers_per_vespene in self.workers_vespene:
                if len(workers_per_vespene[1]) < 3:
                    refinery = self.bot.structures.find_by_tag(workers_per_vespene[0])
                    worker_tag = self.workers_mineral.pop()
                    worker = self.bot.workers.find_by_tag(worker_tag)
                    worker.gather(refinery)
                    workers_per_vespene[1].append(worker_tag)


    def add_unit(self, unit: Unit):
        super().add_unit(unit)

        self.workers_mineral.append(unit.tag)
        mineral = self.bot.mineral_field.find_by_tag(self.mineral_field[random.randrange(0, len(self.mineral_field))])
        unit.gather(mineral)

    def init_workers(self, workers: list[Unit]):
        self.workers_mineral = [ worker.tag for worker in workers ]

    def get_worker(self, near: Point2 = None) -> Unit:
        worker_tag = None
        #todo 默认采气
        if len(self.workers_mineral) > 0:
            worker_tag = self.workers_mineral.pop()
        else:
            for workers_per_vespene in self.workers_vespene:
                if len(workers_per_vespene[1]):
                    worker_tag = workers_per_vespene[1].pop()
                    break
            
        if worker_tag:
            return self.bot.workers.find_by_tag(worker_tag)

    def get_saturation_left(self):
        return len(self.mineral_field) * 2 + 2 - len(self.workers_mineral)

    def get_random_mineral_field(self):
        return self.mineral_field[random.randint(0, len(self.mineral_field) - 1)]
        
    def get_free_vespene(self):
        if len(self.vespene_geyser):
            return self.vespene_geyser[0]

    def on_building_construction_complete(self, unit: Unit):
        if unit.type_id == UnitTypeId.REFINERY:
            for geyser_tag in self.vespene_geyser:
                geyser = self.bot.vespene_geyser.find_by_tag(geyser_tag)
                if geyser.position == unit.position:
                    self.vespene_geyser.remove(geyser_tag)
                    self.workers_vespene.append((unit.tag, []))
                    break

    def on_unit_destroyed(self, unit: Unit):
        if unit.type_id != UnitTypeId.SCV:
            return
        
        if unit.tag in self.workers_mineral:
            self.workers_mineral.remove(unit.tag)
        elif unit.tag in self.workers_vespene:
            self.workers_vespene.remove(unit.tag)

    def debug_string(self) -> str:
        count_workers_vespene = 0
        for workers_per_vespene in self.workers_vespene:
            count_workers_vespene = count_workers_vespene + len(workers_per_vespene[1])

        return "[Mining,M-" + str(len(self.workers_mineral)) + ",V-" + str(count_workers_vespene) + "]"
