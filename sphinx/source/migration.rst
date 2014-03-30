Migrating from SkoolKit 3
=========================
SkoolKit 4 includes some changes that make it incompatible with SkoolKit 3. If
you have developed a disassembly using SkoolKit 3 and find that `skool2html.py`
no longer works with your `skool` files or `ref` files, or produces broken
output, look through the following sections for tips on how to migrate your
disassembly to SkoolKit 4.

[Info]
------
The ``[Info]`` section, introduced in SkoolKit 2.0, is not supported in
SkoolKit 4. If you have one in your `ref` file, copy its contents to the
:ref:`ref-Game` section.
