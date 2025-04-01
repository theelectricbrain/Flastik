[![Build Status](https://travis-ci.org/theelectricbrain/Flastik.svg?branch=master)](https://travis-ci.org/theelectricbrain/Flastik)

[![Pytest](https://github.com/DavidVadnais/Flastik/actions/workflows/pytest.yml/badge.svg)](https://github.com/DavidVadnais/Flastik/actions/workflows/pytest.yml)<p align="center">
   <img align="middle" src='https://raw.githubusercontent.com/theelectricbrain/Flastik/master/flastik/base_templates/default_icon.png' width='250' height='250'>
</p>

# Flastik
Flastik is a tiny-framework for static website design inspired 
by [Flask micro-framework](https://palletsprojects.com/p/flask/).
It provides tools for designing simple static website project 
using Flask-like syntax and project architecture as well as leveraging 
[Jinja2](https://jinja.palletsprojects.com/en/2.10.x/) templating 
system and [Bootstrap](https://getbootstrap.com) "beautyfying" capability. 
Additionally, Flastik aims to ease the porting to Flask if extra 
functionality becomes needed further down your website life cycle. 

In addition, classes and functions have been designed in order to 
ease the management and templating of images, downloads and other 
static files (see StaticFile, Image and Download classes as well as 
collect_static_files function).

## Installation
In order to install Flastik:
 * Change directory to the Flastik code base
 * Run `pip install .`, or `python setup.py install` if you don’t 
   have pip installed on your work station, to install the package 
   (or `sudo python setup.py install`/`sudo pip install .` if root 
   permission is required)
 * Finally run `python setup.py test` to test the sanity of the 
   package installation (or `sudo python setup.py test` if root 
   permission is required)

## Usage
Once Flastik installed, run `flastik --create_doc` from a command
line in order to have access to more detailed documentation.

Similarly, to start up a new flastik project, run `flastik 
--create_project ${PROJECT_NAME}` from a command line.

## License
Flastik is distributed under the GNU GPLv3 License (see LICENSE) and
Bootstrap under the MIT License (see ./flastik/bootstrap/BOOTSTRAP_LICENSE).

