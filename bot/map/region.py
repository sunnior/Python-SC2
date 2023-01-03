from typing import List, Tuple

import numpy
from sc2.position import Point2, Rect


class Region():
    def __init__(self, region_id: int, grid_region : numpy, playable_area : Rect) -> None:
        self.left = 99999
        self.right = 0
        self.height = 0
        self.width = 0
        self.top = 0
        self.bottom = 99999
        self.grid_region = grid_region
        self.playable_area = playable_area
        self.region_id = region_id
        self.townhall_location = None
        self.enemy_topo_distance = 0

        self.regions_nbr: List[Tuple[int, List[Point2]]] = []

    def add_position(self, pos: Point2):
        self.left = min(self.left, pos[0])
        self.right = max(self.right, pos[0])
        self.top = max(self.top, pos[1])
        self.bottom = min(self.bottom, pos[1])
        self.width = self.right - self.left + 1
        self.height = self.top - self.bottom + 1

    def is_in(self, pos: Point2):
        pos_local = pos.offset(Point2((-self.playable_area.x, -self.playable_area.y)))
        return self.grid_region[pos_local.x][pos_local.y] == self.region_id