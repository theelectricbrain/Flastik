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


class CustomInstallCommand(install):
    """Customized setuptools install command - prints a friendly greeting."""
    def run(self):
        install.run(self)
        # Installing scripts manually
        bin_path = os.path.dirname(sys.executable)
        dest = os.path.join(bin_path, 'flastik')
        shutil.copy('./scripts/command_line.py', dest)
        os.chmod(dest, 0o0777)


setup(name='Flastik',
      version='1.0',
      description='A Flask-like Tiny-framework for static websites',
      author='Dr. Thomas Roc',
      author_email='info@electricbrain.fr',
      license='GNU GPLv3',
      # url='https://www.python.org/sigs/distutils-sig/',
      packages=['flastik', 'flastik.scripts'],
      package_dir={'flastik': '', 'flastik.scripts': 'scripts'},
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
      cmdclass={'test': TestCommand, 'install': CustomInstallCommand},
      # FIXME: I cannot get this one to work !!!
      # entry_points={
      #     'console_scripts': ['flastik = flastik.scripts:command_line']
      # },
      # scripts=['scripts/command_line.py']
      )


