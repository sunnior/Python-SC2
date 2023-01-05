#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <numpy/arrayobject.h>
#include <vector>
#include <algorithm>
#include <functional>
#include <map>


class Builder
{
public:
	Builder(PyArrayObject* in_walkable_object, PyArrayObject* in_heights_object)
		: walkable_object(in_walkable_object)
		, heights_object(in_heights_object)
	{
		size_x = (int)walkable_object->dimensions[0];
		size_y = (int)walkable_object->dimensions[1];
	}

	void build();
private:
	void build_distance();
	void build_region();

private:
	PyArrayObject* walkable_object;
	PyArrayObject* heights_object;
	int size_x;
	int size_y;

public:
	PyArrayObject* distance_np;
	PyArrayObject* ridge_np;
	PyArrayObject* region_np;
};

void Builder::build()
{
	build_distance();
	build_region();
}

void Builder::build_distance()
{

	distance_np = (PyArrayObject*)PyArray_SimpleNew(2, walkable_object->dimensions, NPY_UINT8);

	auto is_edge = [&](int x, int y)
	{
		if (x - 1 < 0 || x + 1 > size_x || y - 1 < 0 || y + 1 > size_y)
		{
			return true;
		}
		int new_points[][2] = { {x , y + 1}, {x, y - 1}, {x - 1, y}, {x + 1, y} };
		for (int i = 0; i < 4; ++i)
		{
			npy_uint8* ptr_walk = (npy_uint8*)(walkable_object->data + new_points[i][0] * walkable_object->strides[0] + new_points[i][1] * walkable_object->strides[1]);
			if (*ptr_walk <= 0)
			{
				return true;
			}
		}
		return false;
	};

	std::vector<std::pair<int, int>> scan_points;
	std::vector<std::pair<int, int>> next_scan_points;

	for (int y = 0; y < size_y; ++y)
	{
		for (int x = 0; x < size_x; ++x)
		{
			npy_uint8* ptr = (npy_uint8*)(distance_np->data + x * distance_np->strides[0] + y * distance_np->strides[1]);
			npy_uint8* ptr_walk = (npy_uint8*)(walkable_object->data + x * walkable_object->strides[0] + y * walkable_object->strides[1]);

			if (*ptr_walk)
			{
				*ptr = 99;
				if (is_edge(x, y))
				{
					scan_points.push_back({ x, y });
					*ptr = 1;
				}
			}
			else
			{
				*ptr = 0;
			}
		}
	}

	npy_uint8 distance = 2;
	while (!scan_points.empty())
	{
		while (!scan_points.empty())
		{
			std::pair<int, int> point = scan_points.back();
			scan_points.pop_back();

			int offsets[][2] = { {0, 1}, {0, -1}, {-1, 0}, {1, 0} };
			for (int i = 0; i < 4; ++i)
			{
				int x = point.first + offsets[i][0];
				int y = point.second + offsets[i][1];
				if (x < 0 || x >= size_x || y < 0 || y >= size_y)
				{
					continue;
				}

				npy_uint8* ptr_dis = (npy_uint8*)(distance_np->data + x * distance_np->strides[0] + y * distance_np->strides[1]);
				if (*ptr_dis > distance)
				{
					*ptr_dis = distance;
					int s1 = next_scan_points.size();
					next_scan_points.push_back({ x, y });
				}
			}
		}

		++distance;
		scan_points = std::move(next_scan_points);
	}
}

void Builder::build_region()
{
	ridge_np = (PyArrayObject*)PyArray_SimpleNew(2, walkable_object->dimensions, NPY_UINT8);
	region_np = (PyArrayObject*)PyArray_ZEROS(2, walkable_object->dimensions, NPY_UINT16, 0);

	//get region
	int region_idx = 1;
	auto is_ramp = [&](int x, int y)
	{
		npy_uint8* ptr_height = (npy_uint8*)(heights_object->data + x * heights_object->strides[0] + y * heights_object->strides[1]);
		std::vector<std::pair<int, int>> points_nbr = { {-1, 0}, {1, 0}, {0, -1}, {0, 1} };
		for (auto& point_nbr : points_nbr)
		{
			int x_nbr = point_nbr.first + x;
			int y_nbr = point_nbr.second + y;
			npy_uint8* ptr_dis_nbr = (npy_uint8*)(distance_np->data + x_nbr * distance_np->strides[0] + y_nbr * distance_np->strides[1]);
			if (!*ptr_dis_nbr)
			{
				continue;
			}

			npy_uint8* ptr_height_nbr = (npy_uint8*)(heights_object->data + x_nbr * heights_object->strides[0] + y_nbr * heights_object->strides[1]);

			if (*ptr_height_nbr != *ptr_height)
			{
				return true;
			}

		}
		return false;
	};

	auto is_ridge = [&](int x, int y)
	{
		if (x - 1 < 0 || x + 1 > size_x || y - 1 < 0 || y + 1 > size_y)
		{
			return false;
		}

		npy_uint8* ptr_dis = (npy_uint8*)(distance_np->data + x * distance_np->strides[0] + y * distance_np->strides[1]);
		if (*ptr_dis <= 1)
		{
			return false;
		}

		for (int ix = -1; ix <= 1; ++ix)
		{
			for (int iy = -1; iy <= 1; ++iy)
			{
				if (ix == 0 && iy == 0)
				{
					continue;
				}
				npy_uint8* ptr_dis_nbr = (npy_uint8*)(distance_np->data + (ix + x) * distance_np->strides[0] + (iy + y) * distance_np->strides[1]);
				if (*ptr_dis_nbr > *ptr_dis)
				{
					return false;
				}
			}
		}
		return true;
	};

	std::vector<std::pair<int, int>> ridge_points;
	for (int y = 0; y < size_y; ++y)
	{
		for (int x = 0; x < size_x; ++x)
		{
			npy_uint8* ptr_region = (npy_uint8*)(region_np->data + x * region_np->strides[0] + y * region_np->strides[1]);
			if (*ptr_region)
			{
				continue;
			}

			npy_uint8* ptr_ridge = (npy_uint8*)(ridge_np->data + x * ridge_np->strides[0] + y * ridge_np->strides[1]);
			if (is_ridge(x, y))
			{
				*ptr_ridge = 1;
				ridge_points.push_back(std::pair<int, int>(x, y));
			}
			else
			{
				*ptr_ridge = 0;
			}
		}
	}

	std::sort(ridge_points.begin(), ridge_points.end(), [&](auto& p1, auto& p2) {
		bool is_ramp1 = is_ramp(p1.first, p1.second);
		bool is_ramp2 = is_ramp(p2.first, p2.second);
		if (is_ramp1 != is_ramp2)
		{
			return is_ramp1;
		}

		npy_uint8* ptr_dis1 = (npy_uint8*)(distance_np->data + p1.first * distance_np->strides[0] + p1.second * distance_np->strides[1]);
		npy_uint8* ptr_dis2 = (npy_uint8*)(distance_np->data + p2.first * distance_np->strides[0] + p2.second * distance_np->strides[1]);
		return *ptr_dis1 < *ptr_dis2;
	});

	for (std::pair<int, int>& point : ridge_points)
	{
		npy_uint8* ptr_region = (npy_uint8*)(region_np->data + point.first * region_np->strides[0] + point.second * region_np->strides[1]);
		if (*ptr_region)
		{
			continue;;
		}

		*ptr_region = region_idx;

		bool point_is_ramp = is_ramp(point.first, point.second);
		std::vector<std::pair<int, int>> scan_points, next_scan_points;
		scan_points.push_back(point);

		npy_uint8* ptr_dis_max = (npy_uint8*)(distance_np->data + point.first * distance_np->strides[0] + point.second * distance_np->strides[1]);

		while (scan_points.size())
		{
			for (auto& ipoint : scan_points)
			{
				npy_uint8* ptr_dis = (npy_uint8*)(distance_np->data + ipoint.first * distance_np->strides[0] + ipoint.second * distance_np->strides[1]);
				for (int i = -1; i <= 1; ++i)
				{
					for (int j = -1; j <= 1; ++j)
					{
						if (!i && !j)
						{
							continue;
						}
						int x_nbr = i + ipoint.first;
						int y_nbr = j + ipoint.second;
						npy_uint8* ptr_region_nbr = (npy_uint8*)(region_np->data + x_nbr * region_np->strides[0] + y_nbr * region_np->strides[1]);
						if (*ptr_region_nbr)
						{
							continue;
						}

						if (point_is_ramp && !is_ramp(x_nbr, y_nbr))
						{
							continue;
						}

						npy_uint8* ptr_ridge = (npy_uint8*)(ridge_np->data + x_nbr * ridge_np->strides[0] + y_nbr * ridge_np->strides[1]);
						npy_uint8* ptr_dis_nbr = (npy_uint8*)(distance_np->data + x_nbr * distance_np->strides[0] + y_nbr * distance_np->strides[1]);
						if (*ptr_ridge)
						{
							if (*ptr_dis_nbr > *ptr_dis)
							{
								continue;
							}
						}
						else
						{
							if (*ptr_dis_nbr == 0 || *ptr_dis_nbr >= *ptr_dis)
							{
								continue;
							}
						}

						*ptr_region_nbr = region_idx;
						next_scan_points.push_back(std::pair<int, int>(x_nbr, y_nbr));
					}
				}
			}
			scan_points = std::move(next_scan_points);
		}
		++region_idx;
	}

	//�ϲ�����
	//��������֮������ڹ�ϵ
	std::map<int, std::vector<int>> connects;
	for (int y = 0; y < size_y; ++y)
	{
		for (int x = 0; x < size_x; ++x)
		{
			npy_uint8* ptr_region = (npy_uint8*)(region_np->data + x * region_np->strides[0] + y * region_np->strides[1]);
			if (!*ptr_region)
			{
				continue;
			}

			std::vector<std::pair<int, int>> nbr_points = { { x - 1, y},{ x + 1, y}, {x, y - 1}, {x, y + 1} };
			for (std::pair<int, int>& nbr_point : nbr_points)
			{
				if (nbr_point.first < 0 || nbr_point.first >= size_x || nbr_point.second < 0 || nbr_point.second >= size_y)
				{
					continue;
				}

				npy_uint8* ptr_region_nbr = (npy_uint8*)(region_np->data + nbr_point.first * region_np->strides[0] + nbr_point.second * region_np->strides[1]);
				if (*ptr_region_nbr != 0 && *ptr_region_nbr > *ptr_region)
				{
					auto it = connects.find(*ptr_region);
					if (it != connects.end())
					{
						if (std::find(it->second.begin(), it->second.end(), *ptr_region_nbr) == it->second.end())
						{
							it->second.push_back(*ptr_region_nbr);
						}
					}
					else
					{
						connects.insert(std::pair<int, std::vector<int>>(*ptr_region, { *ptr_region_nbr }));
					}
				}
			}
		}
	}

	//�ϲ�����
	std::map<int, int> single_connect_mapping;
	while (true)
	{
		bool has_new_mapping = false;
		for (auto it = connects.begin(); it != connects.end(); ++it)
		{
			int bigger = 0;
			for (int id : it->second)
			{
				auto it2 = connects.find(id);
				if (it2 == connects.end())
				{
					++bigger;
					continue;
				}

				bool connected_big = false;
				for (int id2 : it2->second)
				{
					if (std::find(it->second.begin(), it->second.end(), id2) != it->second.end())
					{
						connected_big = true;
						break;
					}
				}
				if (!connected_big)
				{
					++bigger;
				}
			}

			if (bigger == 1)
			{
				has_new_mapping = true;
				single_connect_mapping.insert(std::pair<int, int>(it->first, *std::max_element(it->second.begin(), it->second.end())));
				it->second.clear();
				//auto it2 = connects.find(it->second.front());
				//it2->second.erase(std::remove(it2->second.begin(), it2->second.end(), it->first), it2->second.end());
			}
		}

		if (!has_new_mapping)
		{
			break;
		}

		for (auto it = single_connect_mapping.rbegin(); it != single_connect_mapping.rend(); ++it)
		{
			auto it2 = single_connect_mapping.find(it->second);
			while (it2 != single_connect_mapping.end())
			{
				it->second = it2->second;
				it2 = single_connect_mapping.find(it2->second);
			}
		}

		for (auto it = connects.begin(); it != connects.end(); ++it)
		{
			std::vector<int> tmp;
			for (auto it2 = it->second.begin(); it2 != it->second.end(); ++it2)
			{
				int mapping_id = *it2;
				auto it3 = single_connect_mapping.find(*it2);
				if (it3 != single_connect_mapping.end())
				{
					mapping_id = it3->second;
				}

				if (std::find(tmp.begin(), tmp.end(), mapping_id) == tmp.end())
				{
					tmp.push_back(mapping_id);
				}
			}
			it->second = std::move(tmp);
		}

	}

	for (int y = 0; y < size_y; ++y)
	{
		for (int x = 0; x < size_x; ++x)
		{
			npy_uint8* ptr_region = (npy_uint8*)(region_np->data + x * region_np->strides[0] + y * region_np->strides[1]);
			if (!*ptr_region)
			{
				continue;
			}
			auto it = single_connect_mapping.find(*ptr_region);
			if (it != single_connect_mapping.end())
			{
				*ptr_region = it->second;
			}
		}
	}
}


static PyObject* cmap_tool_init(PyObject* self, PyObject* args)
{	
	PyArrayObject* walkable_object;
	PyArrayObject* heights_object;

	if (!PyArg_ParseTuple(args, "OO", &walkable_object, &heights_object))
	{
		return NULL;
	}

	Builder builder(walkable_object, heights_object);
	builder.build();

	//PyObject* return_val;
	//return_val = PyList_New(3);
	//PyList_SetItem(return_val, 0, PyArray_Return(builder.distance_np));
	//PyList_SetItem(return_val, 1, PyArray_Return(builder.ridge_np));
	//PyList_SetItem(return_val, 2, PyArray_Return(builder.region_np));

	//return return_val;
	return PyArray_Return(builder.region_np);
}

static PyMethodDef CMapToolMethods[] = {
    {"init", cmap_tool_init, METH_VARARGS, "init map."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

static struct PyModuleDef cmap_tool_module = {
    PyModuleDef_HEAD_INIT,
    "cmap_tool",   /* name of module */
    NULL, /* module documentation, may be NULL */
    -1,       /* size of per-interpreter state of the module,
                 or -1 if the module keeps state in global variables. */
    CMapToolMethods
};

PyMODINIT_FUNC
PyInit_cmap_tool(void)
{
/*
	size_t total_space = 50 * 1024 * 1024;
	uint8_t* extension_memory = (uint8_t*)malloc(total_space);
	if (!extension_memory) return NULL;

	size_t function_space = (size_t)(0.8 * total_space);
	size_t temp_space = total_space - function_space;

	InitializeMemoryArena(&state.function_arena, function_space, extension_memory);
	InitializeMemoryArena(&state.temp_arena, temp_space, extension_memory + function_space);
*/

	import_array();

    return PyModule_Create(&cmap_tool_module);
}