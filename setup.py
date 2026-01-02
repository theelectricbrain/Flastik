#!/usr/bin/env python
"""
Flastik - A Flask-like Tiny-framework for static websites.
(c) Copyright 2019-2026. See LICENSE for details.
"""
import pytest
from setuptools import setup, Command

with open("README.md", "r") as fh:
    long_description = fh.read()


class TestCommand(Command):
    description = "will run a series of test"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        pytest.main(["./", '--disable-pytest-warnings'])


setup(name='flastik',
      version='1.0.2',
      description='A Flask-like Tiny-framework for static websites',
      long_description=long_description,
      long_description_content_type="text/markdown",
      author='Dr. Thomas Roc',
      author_email='info@electricbrain.fr',
      packages=['flastik'],
      package_dir={'flastik': 'flastik', },
      package_data={'flastik': [
          'README.pdf',
          'LICENSE.txt',
          'base_templates/*',
          'doc_templates/*',
          'bootstrap/css/*',
          'bootstrap/popper/*',
          'bootstrap/jquery/*',
          'bootstrap/js/*', ],
      },
      install_requires=['jinja2', 'docutils', 'pytest'],
      cmdclass={'test': TestCommand},
      scripts=['scripts/flastik'],
      python_requires='>=3.6'
      )

