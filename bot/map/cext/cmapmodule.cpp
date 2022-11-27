#define PY_SSIZE_T_CLEAN
#include <Python.h>

static PyObject* cmap_init(PyObject* self, PyObject* args)
{
    printf("xxxxxxxxxxdfasfds!sdfsda\n");
    return PyUnicode_FromString("text map~!!!!");
}

static PyMethodDef MapMethods[] = {
    {"init", cmap_init, METH_VARARGS, "init map."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

static struct PyModuleDef cmapmodule = {
    PyModuleDef_HEAD_INIT,
    "cmap",   /* name of module */
    NULL, /* module documentation, may be NULL */
    -1,       /* size of per-interpreter state of the module,
                 or -1 if the module keeps state in global variables. */
    MapMethods
};

PyMODINIT_FUNC
PyInit_cmap(void)
{
    return PyModule_Create(&cmapmodule);
}