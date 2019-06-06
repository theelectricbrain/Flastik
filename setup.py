#!/usr/bin/env python
# TODO: define copyright/license
"""
FlasTik - A Flask-like Tiny-framework for static websites.
(c) Copyright 2019. All Rights Reserved. See LICENSE for details.
"""
import pytest
from setuptools import setup, Command


class TestCommand(Command):
    description = "will run a series of test"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        pytest.main(["./"])


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
          'bootstrap/js/*', ]},
      install_requires=['jinja2'],
      cmdclass={'test': TestCommand}
      )
