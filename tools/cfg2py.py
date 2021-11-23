#!/usr/bin/env python3

import configparser
import os
import sys

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write('SKOOLKIT_HOME={}; directory not found\n'.format(SKOOLKIT_HOME))
    sys.exit(1)

SETUP_PY = '''
#!/usr/bin/env python3
from distutils.core import setup

import skoolkit

LONG_DESCRIPTION = """
{long_description}
"""

setup(
    name='{name}',
    version={version},
    author='{author}',
    author_email='{author_email}',
    license='{license}',
    url='{url}',
    description="{description}",
    long_description=LONG_DESCRIPTION,
    packages={packages},
    package_data={package_data},
    scripts={scripts},
    classifiers={classifiers}
)
'''.strip()

c = configparser.ConfigParser()
c.read(f'{SKOOLKIT_HOME}/setup.cfg')
metadata = c['metadata']
options = c['options']
package_data = c['options.package_data']

long_description = metadata['long_description']
if long_description.startswith('file: '):
    with open(f'{SKOOLKIT_HOME}/{long_description[6:]}') as f:
        long_description = f.read().strip()

fields = {
    'name': metadata['name'],
    'version': metadata['version'].strip('attr: '),
    'author': metadata['author'],
    'author_email': metadata['author_email'],
    'license': metadata['license'],
    'url': metadata['url'],
    'description': metadata['description'],
    'long_description': long_description,
    'packages': [p.strip() for p in options['packages'].split(',')],
    'package_data': {k: [d.strip() for d in package_data[k].split(',')] for k in package_data},
    'scripts': [c for c in options['scripts'].split('\n') if c],
    'classifiers': [c for c in metadata['classifiers'].split('\n') if c]
}

print(SETUP_PY.format_map(fields))
