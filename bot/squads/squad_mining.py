
import random
from bot.bot_ai_base import BotAIBase
from bot.squads.squad import Squad
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit

class SquadMining(Squad):

    def __init__(self, bot : BotAIBase, townhall: Unit) -> None:
        super().__init__()
        self.bot = bot
        self.workers_mineral: list[int] = []
        self.workers_vespene: list[tuple[int, list[int]]] = []
        self.townhall = townhall.tag

        expansion_locations_dict = bot.expansion_locations_dict
        resource_list = expansion_locations_dict[townhall.position]
        
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


    def add_worker(self, worker: Unit):
        self.workers_mineral.append(worker.tag)
        mineral = self.bot.mineral_field.find_by_tag(self.mineral_field[random.randrange(0, len(self.mineral_field))])
        worker.gather(mineral)

    def init_workers(self, workers: list[Unit]):
        self.workers_mineral = [ worker.tag for worker in workers ]

    def remove_worker(self):
        #todo 默认采气
        if len(self.workers_mineral) > 0:
            return self.workers_mineral.pop()

        for workers_per_vespene in self.workers_vespene:
            if len(workers_per_vespene[1]) > 0:
                return workers_per_vespene[1].pop()

    def get_saturation_left(self):
        return len(self.mineral_field) * 2 + 2 - len(self.workers_mineral)

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

    def debug_string(self) -> str:
        count_workers_vespene = 0
        for workers_per_vespene in self.workers_vespene:
            count_workers_vespene = count_workers_vespene + len(workers_per_vespene[1])

        return "[Mining,M-" + str(len(self.workers_mineral)) + ",V-" + str(count_workers_vespene) + "]"
