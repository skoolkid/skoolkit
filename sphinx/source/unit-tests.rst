Running unit tests
==================
Unit tests for SkoolKit are included in the `test_*.py` files in the `tests`
directory in the SkoolKit source distribution. To run the unit tests contained
in a single file, open a terminal window, change to the `tests` directory, and
execute the file.

On Windows, the file can be executed by entering its name; for example::

  > test_skoolasm.py

On Linux/\*BSD, the file can be executed by passing it to the Python
interpreter::

  $ python test_skoolasm.py

To run all the unit tests in one go, you can use
`nose <http://somethingaboutorange.com/mrl/projects/nose/>`_.

Once `nose` is installed, run the following command from the `tests`
directory::

  $ nosetests
