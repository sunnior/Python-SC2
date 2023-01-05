from distutils.core import setup, Extension

module1 = Extension('cmap_tool',
                     include_dirs = ['../../../venv/Lib/site-packages/numpy/core/include'], 
                     sources = ['cmap_tool.cpp']
                     )

setup (name = 'cmap_tool',
       version = '1.0',
       description = 'This is a demo package',
       ext_modules = [module1]
       )