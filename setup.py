#!/usr/bin/env python
# TODO: define copyright/license
"""
FlasTik - A Flask-like Tiny-framework for static websites.
(c) Copyright 2019. All Rights Reserved. See LICENSE for details.
"""
from distutils.core import setup

setup(name='Flastic',
      version='1.0',
      description='A Flask-like Tiny-framework for static websites',
      author='Dr. Thomas Roc',
      author_email='info@electricbrain.fr',
      # url='https://www.python.org/sigs/distutils-sig/',
      packages=['flastic'],
      package_dir={'flastic': ''},
      package_data={'flastic': [
            'README.pdf',
            'base_templates/*',
            'bootstrap/css/*',
            'bootstrap/popper/*',
            'bootstrap/jquery/*',
            'bootstrap/js/*',]},
      install_requires=['jinja2'],
      )

