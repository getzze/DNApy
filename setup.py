#!/usr/bin/env python
# -*- coding: utf-8 -*-
import io
import re
import sys

from setuptools import setup, find_packages

# requirements
install_requirements = []

# package informations
with io.open('DNApy/__init__.py', 'r') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]$', f.read(),
                        re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Cannot find version information')

with io.open('README.md', 'r', encoding='utf-8') as f:
    readme = f.read()

with io.open('HISTORY.md', 'r', encoding='utf-8') as f:
    history = f.read()


setup(name='DNApy',
        version=version,
        license='GPL3',
        description='DNA plasmid editing',
        long_description=readme + '\n\n' + history,
        keywords='DNA plasmid',
        packages=find_packages(),
        entry_points={
                'console_scripts': ['DNApy = DNApy.main:DNApy'],
        },
        install_requires=install_requirements,
)
