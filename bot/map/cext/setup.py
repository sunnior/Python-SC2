from distutils.core import setup, Extension

module1 = Extension('map', sources = ['mapmodule.cpp'], extra_compile_args = ["/Od", "/DNDEBUG"])

setup (name = 'map',
       version = '1.0',
       description = 'This is a demo package',
       ext_modules = [module1]
       )