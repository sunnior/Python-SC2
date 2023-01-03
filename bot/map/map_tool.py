from this import s
from typing import Dict
from sc2.bot_ai import BotAI
from cmap_tool import init as cmap_tool_init
import numpy
import matplotlib.pyplot as plt
from bot.map.region import Region
from sc2.position import Point2

class MapTool():
	def __init__(self, bot: BotAI):
		self.bot = bot
		self.regions: Dict[int, Region] = {}

		grid_path = self.bot.game_info.pathing_grid.data_numpy.T
		grid_placement = self.bot.game_info.placement_grid.data_numpy.T
		grid_height = self.bot.game_info.terrain_height.data_numpy.T
		playable_area = self.bot.game_info.playable_area
		playable_origin = Point2((playable_area.x, playable_area.y))

		#不知道为啥，初始的时候path被出生点的矿和基地挡住了
		grid_path = numpy.fmax(grid_path, grid_placement)
		grid_path = grid_path[playable_area.x:(playable_area.width + playable_area.x), playable_area.y:(playable_area.height + playable_area.y)]

		grid_height = numpy.load("test_height_np.npy").astype('uint8')
		grid_height = grid_height[playable_area.x:(playable_area.width + playable_area.x), playable_area.y:(playable_area.height + playable_area.y)]

		self.playable_area = playable_area
		self.grid_region = cmap_tool_init(grid_path, grid_height)
		for x in range(0, playable_area.width):
			for y in range(0, playable_area.height):
				region_id = self.grid_region[x][y]
				if not region_id:
					continue
				if region_id not in self.regions:
					self.regions[region_id] = Region(region_id, self.grid_region, self.playable_area)

				region = self.regions[region_id]
				region.add_position(Point2((x + playable_area.x, y + playable_area.y)))

				points_nbr = [(x-1, y), (x+1, y), (x, y+1), (x, y-1)]
				regions_id_nbr = []
				for point_nbr in points_nbr:
					if point_nbr[0] < 0 or point_nbr[0] >= playable_area.width or point_nbr[1] < 0 or point_nbr[1] >= playable_area.height:
						continue
					
					region_id_nbr = self.grid_region[point_nbr[0]][point_nbr[1]]
					if not region_id_nbr:
						continue

					if region_id_nbr != region_id:
						if region_id_nbr not in regions_id_nbr:
							regions_id_nbr.append(region_id_nbr)

				for region_id_nbr in regions_id_nbr:
					region_nbr = None
					for i_region_nbr in region.regions_nbr:
						if i_region_nbr[0] == region_id_nbr:
							region_nbr = i_region_nbr
							break

					if not region_nbr:
						region_nbr = (region_id_nbr, [])
						region.regions_nbr.append(region_nbr)
					region_nbr[1].append(Point2((x + self.playable_area.x, y + self.playable_area.y)))	

		expansion_locations_list = self.bot.expansion_locations_list
		for expanison_location in expansion_locations_list:
			region_id = self.grid_region[expanison_location.offset(-playable_origin).rounded]
			self.regions[region_id].townhall_location = expanison_location

		enemy_region_id = self.grid_region[self.bot.enemy_start_locations[0].offset(-playable_origin).rounded]
		enemy_region = self.regions[enemy_region_id]
		scaned_regions = [enemy_region_id]
		next_scan_regions = []
		scan_regions = [ region_nbr[0] for region_nbr in enemy_region.regions_nbr ]
		distance = 1
		while len(scan_regions):
			scaned_regions = scaned_regions + scan_regions
			for i_region_id in scan_regions:
				i_region = self.regions[i_region_id]
				i_region.enemy_topo_distance = distance
				for region_nbr in i_region.regions_nbr:
					if region_nbr[0] not in scaned_regions:
						next_scan_regions.append(region_nbr[0])
					
			next_scan_regions, scan_regions = scan_regions, next_scan_regions
			next_scan_regions.clear()
			distance = distance + 1	

		"""
		indices = numpy.indices(self.grid_region.shape)
		x = indices[0].flatten()
		y = indices[1].flatten()
		z = self.grid_region.flatten().astype("float32")

		with numpy.nditer(z, flags=[], op_flags=['readwrite']) as it:
			for iz in it:
				if iz > 0:
					iz[...] = iz * 4 + 40
					
		fig, ax = plt.subplots()
		fig.set_size_inches((10, 10))
		ax.set_facecolor((0, 0, 0))
		plt.scatter(x, y, marker="s", c=z, s=16, linewidths=0.5)

		region_cx = []
		region_cy = []
		region_distance = []
		for region_id in self.regions:
			region = self.regions[region_id]
			cx = region.left + region.width / 2 - self.playable_area.x - 2
			cy = region.bottom + region.height /2 - self.playable_area.y - 2
			region_cx.append(cx)
			region_cy.append(cy)
			region_distance.append(region.enemy_topo_distance)

		for cx, cy, enmey_distance in zip(region_cx, region_cy, region_distance):
			plt.text(cx, cy, str(enmey_distance), color="red", fontsize=12)
			
		plt.show()
		"""

	def get_region(self, location: Point2):
		pos = location.offset(Point2((-self.playable_area.x, -self.playable_area.y))).rounded
		region_id = self.grid_region[pos.x][pos.y]
		return self.regions[region_id]

	def debug(self):

		pathing_grid = self.bot.game_info.pathing_grid
		placement_grid = self.bot.game_info.placement_grid
		terrain_height = self.bot.game_info.terrain_height
		playable_area = self.bot.game_info.playable_area
		playable_np = numpy.array([playable_area.x, playable_area.y, playable_area.width, playable_area.height])

		numpy.save("test_playable_np", playable_np)		
		numpy.save("test_pathing_np", pathing_grid.data_numpy.T)
		numpy.save("test_placement_np", placement_grid.data_numpy.T)
		numpy.save("test_height_np", terrain_height.data_numpy.T)

		"""
        self._vision_blockers: Set[Point2] = bot.game_info.vision_blockers
		"""
		pass

	def test():
		
		#MapTool.test_cpp_back()
		MapTool.test_cpp()
		#MapTool.test_path()
		#MapTool.test_placement()
		#MapTool.test_height()

	def test_cpp():
		playable_area = numpy.load("test_playable_np.npy")
		grid_placement = numpy.load("test_placement_np.npy")
		grid_path = numpy.load("test_pathing_np.npy")

		#不知道为啥，初始的时候path被出生点的矿和基地挡住了
		grid_path = numpy.fmax(grid_path, grid_placement)
		grid_path = grid_path[playable_area[0]:(playable_area[2] + playable_area[0]), playable_area[1]:(playable_area[3] + playable_area[1])]

		grid_height = numpy.load("test_height_np.npy").astype('uint8')
		grid_height = grid_height[playable_area[0]:(playable_area[2] + playable_area[0]), playable_area[1]:(playable_area[3] + playable_area[1])]

		grid_region = cmap_tool_init(grid_path, grid_height)


		"""
		with numpy.nditer(grid_distance, flags=['multi_index'], op_flags=['readwrite']) as it:
			for x in it:
				if x > 0:
					x[...] = x + 4
		indices = numpy.indices(grid_distance.shape)
		x = indices[0].flatten()
		y = indices[1].flatten()
		z = grid_distance.flatten().astype("float32")

		"""
		indices = numpy.indices(grid_region.shape)
		x = indices[0].flatten()
		y = indices[1].flatten()
		z = grid_region.flatten().astype("float32")

		with numpy.nditer(z, flags=[], op_flags=['readwrite']) as it:
			for iz in it:
				if iz > 0:
					iz[...] = iz * 4 + 40
					
		fig, ax = plt.subplots()
		fig.set_size_inches((10, 10))
		ax.set_facecolor((0, 0, 0))
		plt.scatter(x, y, marker="s", c=z, s=16, linewidths=0.5)
		"""
		test_index = numpy.where(grid_ridge == 1)
		#plt.figure(figsize=(10, 10))
		plt.scatter(test_index[0], test_index[1], marker="s", c="red", s=4, linewidths=0.5)
		"""

		plt.show()

	def test_path():
		playable_area = numpy.load("test_playable_np.npy")
		grid_placement = numpy.load("test_placement_np.npy")
		grid_path = numpy.load("test_pathing_np.npy")

		#不知道为啥，初始的时候path被出生点的矿和基地挡住了
		grid_path = numpy.fmax(grid_path, grid_placement)
		grid_path = grid_path[playable_area[0]:(playable_area[2] + playable_area[0]), playable_area[1]:(playable_area[3] + playable_area[1])]
		test_index = numpy.where(grid_path == 1)
		plt.figure(figsize=(10, 10))
		plt.scatter(test_index[0], test_index[1], marker="s", c="red", s=16, linewidths=0.5)
		plt.show()

	def test_placement():
		grid_path = numpy.load("test_placement_np.npy")
		playable_area = numpy.load("test_playable_np.npy")

		grid_path = grid_path[playable_area[0]:(playable_area[2] + playable_area[0]), playable_area[1]:(playable_area[3] + playable_area[1])]
		test_index = numpy.where(grid_path == 1)
		plt.figure(figsize=(10, 10))
		plt.scatter(test_index[0], test_index[1], marker="s", c="red", s=16, linewidths=0.5)
		plt.show()

	def test_height():
		
		playable_area = numpy.load("test_playable_np.npy")
		grid_height = numpy.load("test_height_np.npy").astype('float32')
		grid_height = grid_height[playable_area[0]:(playable_area[2] + playable_area[0]), playable_area[1]:(playable_area[3] + playable_area[1])]
		indices = numpy.indices(grid_height.shape)
		x = indices[0].flatten()
		y = indices[1].flatten()
		z = grid_height.flatten()
		z = z / 255


		fig, ax = plt.subplots()
		fig.set_size_inches((10, 10))
		ax.set_facecolor((0, 0, 0))
		plt.scatter(x, y, marker="s", c=z, s=16, linewidths=0.5)

		plt.show()
