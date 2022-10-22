#!/usr/bin/env python3
from distutils.core import setup
from Cython.Build import cythonize

modules = ('skoolkit/simulator.py', 'skoolkit/loadtracer.py')

setup(ext_modules=cythonize(modules, language_level='3'))
