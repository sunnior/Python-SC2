from setuptools import setup, Extension

module1 = Extension('cmap_tool', sources = ['cmap_tool.cpp'])

setup (name = 'cmap_tool',
       version = '1.0',
       description = 'This is a demo package',
       ext_modules = [module1]
       )