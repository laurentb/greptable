#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='greptable',
    version='1.1.0',
    description='List tables of SQL databases for easy schema greps',
    long_description=open('README').read(),
    author='Laurent Bachelier',
    author_email='laurent@bachelier.name',
    url='http://git.p.engu.in/laurentb/greptable/',
    py_modules=['greptable'],
    test_suite='test',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
    use_2to3=True,
    entry_points={'console_scripts': ['greptable = greptable:main']},
)
