#!/usr/bin/env python
# TODO: define copyright/license
"""
Flastic - A Flask-like pico-framework for static websites.
(c) Copyright 2019. All Rights Reserved. See LICENSE for details.
"""
from distutils.core import setup

setup(name='Flastic',
      version='1.0',
      description='A Flask-like pico-framework for static websites',
      author='Dr. Thomas',
      author_email='troc@hawaii.edu',
      # url='https://www.python.org/sigs/distutils-sig/',
      packages=['flastic'],
      package_dir={'flastic': ''},
      package_data={'flastic': [
            'base_templates/*',
            'bootstrap/css/*',
            'bootstrap/img/*',
            'bootstrap/jquery/*',
            'bootstrap/js/*',]},
      install_requires=['jinja2'],
      py_modules=['flastic']
      )

