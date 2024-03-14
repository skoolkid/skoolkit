from setuptools import Extension, setup

setup(
    ext_modules=[
        Extension("skoolkit.csimulator", ["c/csimulator.c"], optional=True),
        Extension("skoolkit.ccmiosimulator", ["c/csimulator.c"], extra_compile_args=['-DCONTENTION'], optional=True)
    ]
)
