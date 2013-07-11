#!/usr/bin/env python
# -*- coding: utf-8 -*-
from distutils.core import setup

from skoolkit import VERSION

setup(
    name='skoolkit',
    version=VERSION,
    author='Richard Dymond',
    author_email='rjdymond@gmail.com',
    license='GPLv3',
    url='http://pyskool.ca/?page_id=177',
    description="A suite of tools for creating disassemblies of ZX Spectrum games",
    packages=['skoolkit'],
    scripts=['bin2tap.py', 'skool2asm.py', 'skool2ctl.py', 'skool2html.py', 'skool2sft.py', 'sna2skool.py', 'tap2sna.py']
)
