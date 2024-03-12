from setuptools import Extension, setup

setup(
    ext_modules=[Extension("skoolkit.csimulator", ["c/csimulator.c"], optional=True)]
)
