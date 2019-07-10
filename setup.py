#!/usr/bin/env python
"""
Flastik - A Flask-like Tiny-framework for static websites.
(c) Copyright 2019. See LICENSE for details.
"""
import os
import sys
import shutil
import pytest
from setuptools import setup, Command
from setuptools.command.install import install


class TestCommand(Command):
    description = "will run a series of test"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        pytest.main(["./"])


setup(name='Flastik',
      version='1.0',
      description='A Flask-like Tiny-framework for static websites',
      author='Dr. Thomas Roc',
      author_email='info@electricbrain.fr',
      license='GNU GPLv3',
      packages=['flastik'],
      package_dir={'flastik': '', },
      package_data={'flastik': [
          'README.pdf',
          'LICENSE.txt',
          'base_templates/*',
          'doc_templates/*',
          'bootstrap/css/*',
          'bootstrap/popper/*',
          'bootstrap/jquery/*',
          'bootstrap/js/*', ]},
      install_requires=['jinja2', 'docutils'],
      cmdclass={'test': TestCommand},
      scripts=['scripts/flastik']
      )


