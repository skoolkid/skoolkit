============
skool2sft.py
============

SYNOPSIS
========
``skool2sft.py`` [options] FILE

DESCRIPTION
===========
``skool2sft.py`` converts a skool file into a skool file template. The skool
file template is written to stdout. When FILE is '-', ``skool2sft.py`` reads
from standard input.

OPTIONS
=======
-h  Write addresses in hexadecimal format

EXAMPLE
=======
Convert ``game.skool`` into a skool file template named ``game.sft``:

|
|   ``skool2ctl.py game.skool > game.sft``
