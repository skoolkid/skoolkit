from setuptools import Extension, setup
setup(
    py_modules=[], # Ignore any .py files in the current working directory
    ext_modules=[Extension("skoolkit.csimulator", ["csimulator.c"])]
    # ext_modules=[Extension("skoolkit.csimulator", ["csimulator.c"], optional=True)] # Add optional only after extension is known to compile successfully!
)
