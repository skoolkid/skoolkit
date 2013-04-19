#!/usr/bin/env python
# -*- coding: utf-8 -*-
from distutils.core import setup
import shutil

from skoolkit import VERSION

PACKAGE_DIR = 'build/skoolkit-pkg'

shutil.rmtree(PACKAGE_DIR, True)
shutil.copytree('skoolkit', PACKAGE_DIR, ignore=shutil.ignore_patterns('*.pyc', 'manicminer.py', 'jetsetwilly.py'))
shutil.copytree('resources', '{0}/resources'.format(PACKAGE_DIR))

setup(
    name='skoolkit',
    version=VERSION,
    author='Richard Dymond',
    author_email='rjdymond@gmail.com',
    license='GPLv3',
    url='http://pyskool.ca/?page_id=177',
    description="A suite of tools for creating disassemblies of ZX Spectrum games",
    packages=['skoolkit'],
    package_dir={'skoolkit': PACKAGE_DIR},
    package_data={'skoolkit': ['resources/*']},
    scripts=['bin2tap.py', 'skool2asm.py', 'skool2ctl.py', 'skool2html.py', 'skool2sft.py', 'sna2skool.py']
)
