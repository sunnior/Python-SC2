from ast import Num
from tkinter import Grid
from sc2.bot_ai import BotAI
from cmap_tool import init as cmap_tool_init
import numpy
import matplotlib.pyplot as plt

class MapTool():
	def __init__(self, bot: BotAI):
		self.bot = bot

	def debug(self):
		cmap_tool_init()
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

		grid_distance, grid_ridge, grid_region = cmap_tool_init(grid_path, grid_height)


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

		test_index = numpy.where(grid_ridge == 1)
		#plt.figure(figsize=(10, 10))
		plt.scatter(test_index[0], test_index[1], marker="s", c="red", s=4, linewidths=0.5)
		plt.show()

	def test_cpp_back():
		playable_area = numpy.load("test_playable_np.npy")
		grid_placement = numpy.load("test_placement_np.npy")
		grid_path = numpy.load("test_pathing_np.npy")

		#不知道为啥，初始的时候path被出生点的矿和基地挡住了
		grid_path = numpy.fmax(grid_path, grid_placement)
		grid_path = grid_path[playable_area[0]:(playable_area[2] + playable_area[0]), playable_area[1]:(playable_area[3] + playable_area[1])]

		grid_height = numpy.load("test_height_np.npy").astype('float32')
		grid_height = grid_height[playable_area[0]:(playable_area[2] + playable_area[0]), playable_area[1]:(playable_area[3] + playable_area[1])]

		grid_distance = cmap_tool_init(grid_path, grid_height)
		
		indices = numpy.indices(grid_distance.shape)
		x = indices[0].flatten()
		y = indices[1].flatten()
		z = grid_distance.flatten().astype("float32")

		fig, ax = plt.subplots()
		fig.set_size_inches((10, 10))
		ax.set_facecolor((0, 0, 0))
		plt.scatter(x, y, marker="s", c=z, s=16, linewidths=0.5)

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
