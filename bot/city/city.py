import numpy
from MapAnalyzer.MapData import MapData
from MapAnalyzer.Region import Region
from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2, Point3
from sc2.unit import Unit


class City():
    grid_index_null = 0
    grid_index_empty = 1
    grid_index_building = 2

    block_index_null = 0
    block_index_mining_area = 1
    block_index_choke = 2
    block_index_near_base = 3
    block_index_back = 4

    def __init__(self, bot : BotAI, map_data: MapData, region: Region) -> None:
        self.bot = bot
        self.map_data = map_data
        self.region = region
        self.region_left = region.left[0]
        self.region_right = region.right[0]
        self.region_top = region.top[1]
        self.region_bottom = region.bottom[1]
        self.region_width = self.region_right - self.region_left
        self.region_height = self.region_top - self.region_bottom
        self.region_origin = Point2((self.region_left, self.region_bottom))
        self.choke_points: list[Point2] = []

        #表示唯一的，这块地上有什么
        self.grid_build = numpy.zeros((self.region_width, self.region_height)).astype(int)
        self.grid_distance_to_choke = numpy.empty(shape=(self.region_width, self.region_height)).astype(int)
        self.grid_distance_to_choke.fill(1000)
        self.grid_distance_to_edge = numpy.empty(shape=(self.region_width, self.region_height)).astype(int)
        self.grid_distance_to_edge.fill(1000)
        self.grid_road = numpy.zeros((self.region_width, self.region_height)).astype(int)

        self.grid_lock = numpy.zeros(shape=(self.region_width, self.region_height)).astype(int)
        self.grid_blocks = numpy.zeros(shape=(self.region_width, self.region_height)).astype(int)

        self._cal_grid_base()
        self._cal_grid_resources()
        self._cal_distance_to_edge()
        self._cal_distance_to_choke()

        self._cal_block_choke()
        self._cal_block_mining()
        self._cal_block_back()
        self._cal_block_base()

    def _cal_grid_base(self):
        # placement_grid = self.map_data.placement_arr.T
        for world_point in self.region.buildables.points:
            local_point = world_point.offset(-self.region_origin)
            self.grid_build[local_point[0]][local_point[1]] = City.grid_index_empty

    def _cal_grid_resources(self):

        townhall = self.bot.townhalls[0]
        expansion_locations_dict = self.bot.expansion_locations_dict
        resource_list = expansion_locations_dict[townhall.position]
        for mineral_field in resource_list.mineral_field:
            mineral_pos = mineral_field.position.offset(Point2((-1, 0))).rounded
            local_pos = mineral_pos.offset(-self.region_origin)
            for x in range(local_pos[0], local_pos[0] + 2):
                self.grid_build[x][local_pos[1]] = City.grid_index_building

            for x in range(local_pos[0] - 1, local_pos[0] + 3):
                for y in range(local_pos[1] - 1, local_pos[1] + 2):
                    #todo 不知道为啥矿的周围有洞
                    if self.grid_build[x][y] != City.grid_index_building:
                        self.grid_build[x][y] = City.grid_index_empty

        for vespene_geyser in resource_list.vespene_geyser:
            vespene_geyser_center = vespene_geyser.position.rounded
            vespene_geyser_pos = vespene_geyser.position.offset(Point2((-1.5, -1.5))).rounded
            local_pos = vespene_geyser_pos.offset(-self.region_origin)

            for x in range(local_pos[0], local_pos[0] + 3):
                for y in range(local_pos[1], local_pos[1] + 3):
                    self.grid_build[x][y] = City.grid_index_building

        townhall_position = townhall.position.offset(Point2((-2.5, -2.5))).rounded
        local_townhall_pos = townhall_position.offset(-self.region_origin)

        #todo 我也不知道为什么，在基地的周围会有一圈空的
        for x in range(local_townhall_pos[0] - 1, local_townhall_pos[0] + 6):
            for y in range(local_townhall_pos[1] - 1, local_townhall_pos[1] + 6):
                self.grid_build[x][y] = City.grid_index_empty

        for x in range(local_townhall_pos[0], local_townhall_pos[0] + 5):
            for y in range(local_townhall_pos[1], local_townhall_pos[1] + 5):
                self.grid_build[x][y] = City.grid_index_building

    def _cal_block_back(self):
        townhall = self.bot.townhalls[0]
        expansion_locations_dict = self.bot.expansion_locations_dict
        resource_list = expansion_locations_dict[townhall.position]

        scan_points = []
        next_scan_points = []
        for mineral_field in resource_list.mineral_field:
            mineral_pos = mineral_field.position.offset(Point2((-1, 0))).rounded
            local_pos = mineral_pos.offset(-self.region_origin)
            for x in range(local_pos[0], local_pos[0] + 2):
                scan_points.append(Point2((x, local_pos[1])))

        while len(scan_points):
            for point in scan_points:
                if self.grid_build[point[0]][point[1]] == City.grid_index_empty:
                    self.grid_blocks[point[0]][point[1]] = City.block_index_back
                    self.grid_road[point[0]][point[1]] = 0

                distance_to_edge = self.grid_distance_to_edge[point[0]][point[1]]
                new_points = []
                for x in range(point[0] - 1, point[0] + 2):
                    for y in range(point[1] - 1, point[1] + 2):
                        new_points.append(Point2((x, y)))
                for new_point in new_points:
                    if not self.is_point_in_region_box(new_point):
                        continue

                    if self.grid_blocks[new_point[0]][new_point[1]] != City.block_index_null:
                        continue

                    if self.grid_distance_to_edge[new_point[0]][new_point[1]] >= distance_to_edge:
                        if self.grid_build[new_point[0]][new_point[1]] == City.grid_index_empty:
                            self.grid_road[new_point[0]][new_point[1]] = 1
                        continue
                    
                    next_scan_points.append(new_point)

            scan_points.clear()
            scan_points, next_scan_points = next_scan_points, scan_points    
        
    def _cal_block_base(self):
        extend = 8
        townhall = self.bot.townhalls[0]
        townhall_position = townhall.position.offset(Point2((-2.5, -2.5))).rounded
        local_townhall_pos = townhall_position.offset(-self.region_origin)

        bound_min = Point2((local_townhall_pos[0] - extend, local_townhall_pos[1] - extend))
        bound_max = Point2((local_townhall_pos[0] + 5 + extend, local_townhall_pos[1] + 5 + extend))

        scan_points = []
        for x in range(local_townhall_pos[0] - 1, local_townhall_pos[0] + 6):
            for y in range(local_townhall_pos[1] - 1, local_townhall_pos[1] + 6):
                point = Point2((x, y))
                if self.grid_build[x][y] == City.grid_index_empty and self.grid_blocks[x][y] == City.block_index_null:
                    scan_points.append(point)
                    self.grid_blocks[x][y] = City.block_index_near_base

        next_scan_points = []
        while len(scan_points):
            for point in scan_points:
                new_points = [ point.offset(Point2((-1, 0))),point.offset(Point2((1, 0))), point.offset(Point2((0, 1))), point.offset(Point2((0, -1))) ] 
                for new_point in new_points:
                    if (
                        not self.is_point_in_region_box(new_point) or
                        self.grid_build[new_point[0]][new_point[1]] != City.grid_index_empty or
                        self.grid_blocks[new_point[0]][new_point[1]] != City.block_index_null or
                        self.grid_distance_to_edge[new_point[0]][new_point[1]] < 2 or
                        self.grid_road[new_point[0]][new_point[1]]
                    ):
                        continue                    

                    #if new_point[0] < bound_min[0] or new_point[0] > bound_max[0] or new_point[1] < bound_min[1] or new_point[1] > bound_max[1]:
                        #continue
                    
                    self.grid_blocks[new_point[0]][new_point[1]] = City.block_index_near_base
                    next_scan_points.append(new_point)

            scan_points.clear()
            next_scan_points, scan_points = scan_points, next_scan_points

    def _cal_block_choke(self):
        choke_points_x = [ point[0] for point in self.choke_points ]
        choke_points_y = [ point[1] for point in self.choke_points ]
        
        choke_min_x = min(choke_points_x)
        choke_max_x = max(choke_points_x)
        choke_min_y = min(choke_points_y)
        choke_max_y = max(choke_points_y)
    
        choke_min_x_ex = min(choke_min_x, choke_max_x - 6)
        choke_max_x_ex = max(choke_max_x, choke_min_x + 6)
        choke_max_y_ex = max(choke_max_y, choke_min_y + 6)
        choke_min_y_ex = min(choke_min_y, choke_max_y - 6)

        for x in range(choke_min_x_ex - 2, choke_max_x_ex + 1 + 2):
            for y in range(choke_min_y_ex - 2, choke_max_y_ex + 1 + 2):
                if x < choke_min_x_ex or x > choke_max_x_ex or y < choke_min_y_ex or y > choke_max_y_ex:
                    if self.is_point_in_region_box(Point2((x, y))) and self.grid_build[x][y] == City.grid_index_empty:
                        self.grid_road[x][y] = 1
                        continue

                if self.is_point_in_region_box(Point2((x, y))) and self.grid_build[x][y] != City.grid_index_null:
                    self.grid_blocks[x][y] = City.block_index_choke        

    def _cal_block_mining(self):
        townhall = self.bot.townhalls[0]
        townhall_center = townhall.position.rounded.offset(-self.region_origin)
        expansion_locations_dict = self.bot.expansion_locations_dict
        resource_list = expansion_locations_dict[townhall.position]

        resources_positions: list[Point2] =[]
        for mineral_field in resource_list.mineral_field:
            mineral_pos = mineral_field.position
            local_pos = mineral_pos.offset(-self.region_origin)
            resources_positions.append(local_pos)

        for vespene_geyser in resource_list.vespene_geyser:
            vespene_geyser_center = vespene_geyser.position
            local_pos = vespene_geyser_center.offset(-self.region_origin)
            resources_positions.append(local_pos)

        for position in resources_positions:
            test_points = []
            while position.distance_to(townhall_center) > 2:
                position = position.towards(townhall_center)
                test_points.append(position.rounded)

            for point in test_points:
                for x in range(point[0] - 1, point[0] + 2):
                    for y in range(point[1] - 1, point[1] + 2):
                        self.grid_blocks[x][y] = City.block_index_mining_area
                        self.grid_road[x][y] = 1

    def _cal_distance_to_edge(self):
        def is_edge_point(point: Point2):
            new_points = [ point.offset(Point2((-1, 0))),point.offset(Point2((1, 0))), point.offset(Point2((0, 1))), point.offset(Point2((0, -1))) ] 
            for point in new_points:
                if not self.is_point_in_region_box(point) or self.grid_build[point[0]][point[1]] == City.grid_index_null:
                    return True

            return False

        scan_points = []
        next_scan_points = []
        for x in range(0, self.region_width):
            for y in range(0, self.region_height):
                if self.grid_build[x][y] == City.grid_index_null:
                    continue

                if is_edge_point(Point2((x, y))):
                    scan_points.append(Point2((x, y)))
                    self.grid_distance_to_edge[x][y] = 0
                
        distance = 1
        while len(scan_points):
            for point in scan_points:
                new_points = [ point.offset(Point2((-1, 0))),point.offset(Point2((1, 0))), point.offset(Point2((0, 1))), point.offset(Point2((0, -1))) ]
                for new_point in new_points: 
                    if  not self.is_point_in_region_box(new_point) or self.grid_build[new_point[0]][new_point[1]] == City.grid_index_null:
                            continue
                        
                    if self.grid_distance_to_edge[new_point[0]][new_point[1]] > distance:
                        self.grid_distance_to_edge[new_point[0]][new_point[1]] = distance
                        next_scan_points.append(new_point)

            distance = distance + 1
            scan_points.clear()
            scan_points, next_scan_points = next_scan_points, scan_points

    def _cal_distance_to_choke(self):

        choke = self.region.region_chokes[0]
        choke_points = choke.buildables.points
        for choke_point in choke_points:
            choke_point_local = choke_point.offset(-self.region_origin)
            if choke_point_local[0] < 0 or choke_point_local[0] >= self.region_width:
                continue
            if choke_point_local[1] < 0 or choke_point_local[1] >= self.region_height:
                continue

            if self.grid_build[choke_point_local[0]][choke_point_local[1]] == 1:
                self.choke_points.append(choke_point_local)
                self.grid_distance_to_choke[choke_point_local[0]][choke_point_local[1]] = 0

        scan_points = self.choke_points.copy()
        next_scan_points: list[Point2] = []

        grid_scaned = numpy.zeros(shape=(self.region_width, self.region_height)).astype(int)
        for point in scan_points:
            grid_scaned[point[0]][point[1]] = 1

        distance = 1
        while len(scan_points) > 0:
            for point in scan_points:
                new_points = [ point.offset(Point2((-1, 0))),point.offset(Point2((1, 0))), point.offset(Point2((0, 1))), point.offset(Point2((0, -1))) ] 
                new_points = [ new_point for new_point in new_points if self.is_point_in_region_box(new_point) and 
                                                                        self.grid_build[new_point[0]][new_point[1]] == City.grid_index_empty and 
                                                                        grid_scaned[new_point[0]][new_point[1]] == 0]
                for new_point in new_points:
                    grid_scaned[new_point[0]][new_point[1]] = 1
                    self.grid_distance_to_choke[new_point[0]][new_point[1]] = distance

                next_scan_points = next_scan_points + new_points                 

            scan_points.clear()
            scan_points, next_scan_points = next_scan_points, scan_points

            distance = distance + 1

    def terrain_to_z_height(self, h):
        """Gets correct z from versions 4.9.0+"""
        return -16 + 32 * h / 255

    def is_point_in_region_box(self, point: Point2) -> bool:
        if point[0] < 0 or point[0] >= self.region_width:
            return False
        if point[1] < 0 or point[1] >= self.region_height:
            return False    
        return True

    def is_point_buildable(self, point: Point2) -> bool:
        if not self.is_point_in_region_box(point):
            return False
        
        if self.grid_build[point[0]][point[1]] != City.grid_index_empty or self.grid_lock[point[0]][point[1]] != 0 or self.grid_road[point[0]][point[1]]:
            return False

        return True

    def lock_positions(self, point_left_bottom: Point2, size: Point2):
        position_origin = point_left_bottom.offset(-self.region_origin)
        for x in range(position_origin[0], position_origin[0] + size[0]):
            for y in range(position_origin[1], position_origin[1] + size[1]):
                self.grid_lock[x][y] = 1

    def unlock_positions(self, point_left_bottom: Point2, size: Point2):
        position_origin = point_left_bottom.offset(-self.region_origin)
        for x in range(position_origin[0], position_origin[0] + size[0]):
            for y in range(position_origin[1], position_origin[1] + size[1]):
                self.grid_lock[x][y] = 0

    async def get_placement_near_base(self, unit_type: UnitTypeId, max_to_choke_distance = 25, has_addon = False):
        unit_data = self.bot.game_data.units[unit_type.value]
        creation_ability = unit_data.creation_ability.id
        radius = unit_data.footprint_radius

        grid_scaned = numpy.zeros(shape=(self.region_width, self.region_height)).astype(int)
        building_size: Point2 = Point2((int(radius * 2),  int(radius * 2)))
        building_size_half: Point2 = Point2((radius,  radius))

        base_center = self.bot.start_location.rounded.offset(-self.region_origin)
        scan_points = [base_center]
        next_scan_points: list[Point2] = []
        for point in scan_points:
            grid_scaned[point[0]][point[1]] = 1

        def check_grid(point, building_size):
            for x in range(point[0], point[0] + building_size[0]):
                for y in range(point[1], point[1] + building_size[1]):
                    if not self.is_point_buildable(Point2((x, y))):
                        return False

            return True

        while len(scan_points) > 0:
            possible_points = []

            for point in scan_points:
                
                distance = self.grid_distance_to_choke[point[0]][point[1]]
                can_build = False
                if distance <= max_to_choke_distance:
                    can_build = check_grid(point, building_size)
                
                if can_build and has_addon:
                    add_position = Point2((point[0] + building_size[0], point[1]))
                    can_build = check_grid(add_position, Point2((2, 2)))
                
                if can_build:
                    possible_points.append(point.offset(self.region_origin).offset(building_size_half))

                new_points = [ point.offset(Point2((-1, 0))),point.offset(Point2((1, 0))), point.offset(Point2((0, 1))), point.offset(Point2((0, -1))) ] 
                #todo 后面如果保证了连通就可以再这里加上检查是否可以通过，才扩展
                new_points = [ new_point for new_point in new_points if self.is_point_in_region_box(new_point) and 
                                                                        grid_scaned[new_point[0]][new_point[1]] == 0]
                for new_point in new_points:
                    grid_scaned[new_point[0]][new_point[1]] = 1                                            
                next_scan_points = next_scan_points + new_points    

            if len(possible_points) > 0:
                res = await self.bot.client._query_building_placement_fast(creation_ability, possible_points)
                possible = [p for r, p in zip(res, possible_points) if r]

                if has_addon:
                    # Filter remaining positions if addon can be placed
                    res = await self.bot.client._query_building_placement_fast(
                        AbilityId.TERRANBUILD_SUPPLYDEPOT,
                    [p.offset((2.5, -0.5)) for p in possible])
                    possible = [p for r, p in zip(res, possible) if r]

                if possible:
                    position = possible[0]
                    return position

            scan_points.clear()
            scan_points, next_scan_points = next_scan_points, scan_points
            distance = distance + 1

        assert(False)
        return None                

    async def get_placement_near_choke(self, unit_type: UnitTypeId, start_distance = 0, has_addon = False):

        unit_data = self.bot.game_data.units[unit_type.value]
        creation_ability = unit_data.creation_ability.id
        radius = unit_data.footprint_radius

        grid_scaned = numpy.zeros(shape=(self.region_width, self.region_height)).astype(int)

        building_size: Point2 = Point2((int(radius * 2),  int(radius * 2)))
        building_size_half: Point2 = Point2((radius,  radius))
        
        scan_points = self.choke_points.copy()
        next_scan_points: list[Point2] = []
        for point in scan_points:
            grid_scaned[point[0]][point[1]] = 1

        def check_grid(point, building_size):
            for x in range(point[0], point[0] + building_size[0]):
                for y in range(point[1], point[1] + building_size[1]):
                    if not self.is_point_buildable(Point2((x, y))):
                        return False

            return True

        while len(scan_points) > 0:
            distance = self.grid_distance_to_choke[scan_points[0][0]][scan_points[0][1]]
            possible_points = []

            for point in scan_points:
                
                can_build = check_grid(point, building_size)
                if can_build and has_addon:
                    add_position = Point2((point[0] + building_size[0], point[1]))
                    can_build = check_grid(add_position, Point2((2, 2)))
                
                if can_build:
                    possible_points.append(point.offset(self.region_origin).offset(building_size_half))

                new_points = [ point.offset(Point2((-1, 0))),point.offset(Point2((1, 0))), point.offset(Point2((0, 1))), point.offset(Point2((0, -1))) ] 
                #todo 后面如果保证了连通就可以再这里加上检查是否可以通过，才扩展
                new_points = [ new_point for new_point in new_points if self.is_point_in_region_box(new_point) and 
                                                                        grid_scaned[new_point[0]][new_point[1]] == 0]
                for new_point in new_points:
                    grid_scaned[new_point[0]][new_point[1]] = 1                                            
                next_scan_points = next_scan_points + new_points    

            if len(possible_points) > 0 and distance >= start_distance:
                res = await self.bot.client._query_building_placement_fast(creation_ability, possible_points)
                possible = [p for r, p in zip(res, possible_points) if r]

                if has_addon:
                    # Filter remaining positions if addon can be placed
                    res = await self.bot.client._query_building_placement_fast(
                        AbilityId.TERRANBUILD_SUPPLYDEPOT,
                    [p.offset((2.5, -0.5)) for p in possible])
                    possible = [p for r, p in zip(res, possible) if r]

                if possible:
                    position = possible[0]
                    return position

            scan_points.clear()
            scan_points, next_scan_points = next_scan_points, scan_points
            distance = distance + 1

        assert(False)
        return None

    async def get_placement_far_choke(self, unit_type: UnitTypeId, has_addon = False):
        unit_data = self.bot.game_data.units[unit_type.value]
        creation_ability = unit_data.creation_ability.id
        radius = unit_data.footprint_radius

        grid_scaned = numpy.zeros(shape=(self.region_width, self.region_height)).astype(int)

        building_size: Point2 = Point2((int(radius * 2),  int(radius * 2)))
        building_size_half: Point2 = Point2((radius,  radius))
        
        shape = self.grid_build.shape
        max_distance = 0 
        scan_points: list[Point2] = []
        next_scan_points: list[Point2] = []

        for x in range(0, shape[0]):
            for y in range(0, shape[1]):
                if self.grid_build[x][y] != City.grid_index_empty:
                    continue

                distance = self.grid_distance_to_choke[x][y]
                if distance > max_distance:
                    max_distance = distance
                    scan_points.clear()
                    scan_points.append(Point2((x, y)))
                elif distance == max_distance:
                    scan_points.append(Point2((x, y)))

        for point in scan_points:
            grid_scaned[point[0]][point[1]] = 1

        def check_grid(point, building_size):
            for x in range(point[0], point[0] + building_size[0]):
                for y in range(point[1], point[1] + building_size[1]):
                    if not self.is_point_buildable(Point2((x, y))):
                        return False

            return True

        while len(scan_points) > 0:
            distance = self.grid_distance_to_choke[scan_points[0][0]][scan_points[0][1]]
            possible_points = []

            for point in scan_points:
                
                can_build = check_grid(point, building_size)
                if can_build and has_addon:
                    add_position = Point2((point[0] + building_size[0], point[1]))
                    can_build = check_grid(add_position, Point2((2, 2)))
                
                if can_build:
                    possible_points.append(point.offset(self.region_origin).offset(building_size_half))

                new_points = [ point.offset(Point2((-1, 0))),point.offset(Point2((1, 0))), point.offset(Point2((0, 1))), point.offset(Point2((0, -1))) ] 
                #todo 后面如果保证了连通就可以再这里加上检查是否可以通过，才扩展
                new_points = [ new_point for new_point in new_points if self.is_point_in_region_box(new_point) and 
                                                                        grid_scaned[new_point[0]][new_point[1]] == 0]
                for new_point in new_points:
                    grid_scaned[new_point[0]][new_point[1]] = 1                                            
                next_scan_points = next_scan_points + new_points    

            if len(possible_points) > 0:
                res = await self.bot.client._query_building_placement_fast(creation_ability, possible_points)
                possible = [p for r, p in zip(res, possible_points) if r]

                if has_addon:
                    # Filter remaining positions if addon can be placed
                    res = await self.bot.client._query_building_placement_fast(
                        AbilityId.TERRANBUILD_SUPPLYDEPOT,
                    [p.offset((2.5, -0.5)) for p in possible])
                    possible = [p for r, p in zip(res, possible) if r]

                if possible:
                    position = possible[0]
                    return position

            scan_points.clear()
            scan_points, next_scan_points = next_scan_points, scan_points
            distance = distance + 1

        assert(False)
        return None

    def on_building_complete(self, unit: Unit):
        position = unit.position
        radius = unit.footprint_radius
        building_size_half = Point2((radius, radius))
        building_size = Point2((radius * 2, radius * 2)).rounded
        position_local = position.offset(-self.region_origin).offset(-building_size_half).rounded
        for x in range(position_local[0], position_local[0] + building_size[0]):
            for y in range(position_local[1], position_local[1] + building_size[1]):
                if self.is_point_in_region_box(Point2((x, y))):
                    self.grid_build[x][y] = City.grid_index_building
    
    def debug(self):
        terrain_height = self.map_data.terrain_height.copy().T
        if_show_distance_to_choke = False
        if_show_distance_to_edge = False
        if_show_block_id = True

        for y in range(0, self.region_height):
            for x in range(0, self.region_width):
                world_point = Point2((x, y)).offset(self.region_origin)
                height = max(self.terrain_to_z_height(terrain_height[world_point]), 
                            self.terrain_to_z_height(terrain_height[world_point.offset(Point2((1, 0)))]), 
                            self.terrain_to_z_height(terrain_height[world_point.offset(Point2((0, 1)))]))
                
                if if_show_distance_to_choke:
                    distance = self.grid_distance_to_choke[x][y]
                    if distance < 100:
                        in_point = Point3((world_point[0] + 0.5, world_point[1] + 0.5, height + 0.45))
                        self.bot.client.debug_text_world(str(distance), in_point, (255, 255, 255))
                elif if_show_distance_to_edge:
                    distance = self.grid_distance_to_edge[x][y]
                    if distance < 100:
                        in_point = Point3((world_point[0] + 0.5, world_point[1] + 0.5, height + 0.45))
                        self.bot.client.debug_text_world(str(distance), in_point, (255, 255, 255))
                elif if_show_block_id:
                    id = self.grid_blocks[x][y]
                    if id:
                        in_point = Point3((world_point[0] + 0.5, world_point[1] + 0.5, height + 0.45))
                        self.bot.client.debug_text_world(str(id), in_point, (255, 255, 255))                

                
                grid_value = self.grid_build[x][y]
                block_value = self.grid_blocks[x][y]
                
                if grid_value != City.grid_index_null:
                    in_color = (255, 255, 255)
                    if block_value:
                        in_color = (0, 255, 255)
                    else:
                        in_color = (0, 255, 0)

                    if self.grid_road[x][y]:
                        in_color = (255, 0, 255)
                    
                    if grid_value == City.grid_index_building:
                        in_color = (255, 0, 0)

                    in_point = Point3((world_point[0] + 0.5, world_point[1] + 0.5, height))
                    self.bot.client.debug_box2_out(in_point, half_vertex_length=0.45, color=in_color)

                if self.grid_lock[x][y]:
                    in_point = Point3((world_point[0] + 0.5, world_point[1] + 0.5, height))
                    self.bot.client.debug_box2_out(in_point, half_vertex_length=0.35, color=(255, 255, 0))

                            
