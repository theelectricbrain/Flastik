#!/usr/bin/env python
"""
Flastik - A Flask-like Tiny-framework for static websites.
(c) Copyright 2019. See LICENSE for details.
"""
import os
import shutil
import sys
from argparse import ArgumentParser
from glob import glob
# Templating imports
from flastik import Builder, render_template
# Static files imports
from flastik import Image, Download, collect_static_files
# Argument parsers imports
from flastik import (add_Builder_arguments, add_build_arguments,
                      add_collect_static_files_arguments)


# General context for navbar and footer
dest = "test_build"
context = {
    'project_name': 'project_name',
    'navbar_links': [
        {'name': 'home', 'url': "?"},
        {'name': 'test', 'url': 'https://github.com/theelectricbrain'},
    ],
    'footer_link': {'name': 'Flastik - Copyright 2019', 'url': 'https://github.com/theelectricbrain'},
}

ship_list = ["Shippy-MacShipface", "Boatty-MacBoatface"]
cruise_dict = {"Shippy-MacShipface": [1, 2], "Boatty-MacBoatface": [99, 98, 97]}

# Testing benchmarks
hello_world_str = """<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Meta -->
    <meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    
    <!-- Favicon -->
    <link rel="shortcut icon" href="static/favicon.ico">
    <!-- Bootstrap CSS -->
	<link href="static/css/bootstrap.min.css" rel="stylesheet" type='text/css'>
    <!-- Custom CSS stylesheet -->
    <link href="static/stylesheet.css" rel="stylesheet" type='text/css'>
    <!-- Block Title -->
    <title>Hello World !</title>
    <!-- Block Header -->
    
</head>

<!-- Block Title -->
<body>
    
<!-- Navigation -->

<nav class="navbar fixed-top navbar-expand-lg navbar-light bg-light">
  <a class="navbar-brand" href="#">
    <img src="static/favicon.ico" width="30" height="30" alt="">
    project_name
  </a>
  <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
    <span class="navbar-toggler-icon"></span>
  </button>

  <!-- Everything you want hidden at 940px or less, place within here -->
  <div class="collapse navbar-collapse" id="navbarSupportedContent">
    <ul class="navbar-nav mr-auto">
      
      <li class="nav-item active">
        <a class="nav-link" href="?">home</a>
      </li>
      
      <li class="nav-item active">
        <a class="nav-link" href="https://github.com/theelectricbrain">test</a>
      </li>
      

    </ul>
  </div>
</nav>


    <h2>Hello World !</h2>
<br><a href='Shippy-MacShipface/cruise/1/report/index.html'>Shippy-MacShipface: report for cruise 1</a>
<br><a href='Shippy-MacShipface/cruise/2/report/index.html'>Shippy-MacShipface: report for cruise 2</a>
<br><a href='Boatty-MacBoatface/cruise/99/report/index.html'>Boatty-MacBoatface: report for cruise 99</a>
<br><a href='Boatty-MacBoatface/cruise/98/report/index.html'>Boatty-MacBoatface: report for cruise 98</a>
<br><a href='Boatty-MacBoatface/cruise/97/report/index.html'>Boatty-MacBoatface: report for cruise 97</a>
    <br><h3><a href='downloads/README.pdf' download>README</a></h3>
    <br><h3>Default Icon: </h3><img src="images/test/something_else.png" class="img-fluid" alt="Default Icon">
    <br><h3>Testing url_for from Template: "Home" = hello_world.html</h3>
    <br>
    <h3>
        <a href="Shippy-MacShipface/cruise/1/report/index.html">
            Testing url_for from Template: "Report Cruise 1 for Shippy MacShipface"
        </a>
    </h3>
<!-- Footer -->
<div id="footer">
    <div>
        <div><a href="https://github.com/theelectricbrain">Flastik - Copyright 2019</a></div>
    </div>
</div>

    <!-- JQuery -->
    <script type="text/javascript" src="static/jquery/jquery-3.4.1.min.js"></script>
    <!-- Popper -->
    <script type="text/javascript" src="static/popper/popper.min.js "></script>
    <!-- Bootstrap  Core JavaScript -->
    <script type="text/javascript" src="static/js/bootstrap.min.js"></script>
</body>

</html>"""

cruise_str = """<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Meta -->
    <meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    
    <!-- Favicon -->
    <link rel="shortcut icon" href="../../../static/favicon.ico">
    <!-- Bootstrap CSS -->
	<link href="../../../static/css/bootstrap.min.css" rel="stylesheet" type='text/css'>
    <!-- Custom CSS stylesheet -->
    <link href="../../../static/stylesheet.css" rel="stylesheet" type='text/css'>
    <!-- Block Title -->
    <title>Shippy-MacShipface: Cruise 1</title>
    <!-- Block Header -->
    
</head>

<!-- Block Title -->
<body>
    
<!-- Navigation -->

<nav class="navbar fixed-top navbar-expand-lg navbar-light bg-light">
  <a class="navbar-brand" href="#">
    <img src="../../../static/favicon.ico" width="30" height="30" alt="">
    project_name
  </a>
  <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
    <span class="navbar-toggler-icon"></span>
  </button>

  <!-- Everything you want hidden at 940px or less, place within here -->
  <div class="collapse navbar-collapse" id="navbarSupportedContent">
    <ul class="navbar-nav mr-auto">
      
      <li class="nav-item active">
        <a class="nav-link" href="../../../hello_world.html">home</a>
      </li>
      
      <li class="nav-item active">
        <a class="nav-link" href="https://github.com/theelectricbrain">test</a>
      </li>
      

    </ul>
  </div>
</nav>


    <h2>This cruise 1. Hail to the Shippy-MacShipface !</h2>
    
    <br><h3>Default Icon: </h3><img src="../../../images/test/something_else.png" class="img-fluid" alt="Default Icon">
    <br><h3>Testing url_for from Template: "Home" = ../../../hello_world.html</h3>
    <br>
    <h3>
        <a href="report/index.html">
            Testing url_for from Template: "Report Cruise 1 for Shippy MacShipface"
        </a>
    </h3>
<!-- Footer -->
<div id="footer">
    <div>
        <div><a href="https://github.com/theelectricbrain">Flastik - Copyright 2019</a></div>
    </div>
</div>

    <!-- JQuery -->
    <script type="text/javascript" src="../../../static/jquery/jquery-3.4.1.min.js"></script>
    <!-- Popper -->
    <script type="text/javascript" src="../../../static/popper/popper.min.js "></script>
    <!-- Bootstrap  Core JavaScript -->
    <script type="text/javascript" src="../../../static/js/bootstrap.min.js"></script>
</body>

</html>"""


cruise_n_data_str = """<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Meta -->
    <meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    
    <!-- Favicon -->
    <link rel="shortcut icon" href="../../../../static/favicon.ico">
    <!-- Bootstrap CSS -->
	<link href="../../../../static/css/bootstrap.min.css" rel="stylesheet" type='text/css'>
    <!-- Custom CSS stylesheet -->
    <link href="../../../../static/stylesheet.css" rel="stylesheet" type='text/css'>
    <!-- Block Title -->
    <title>data - Shippy-MacShipface</title>
    <!-- Block Header -->
    
</head>

<!-- Block Title -->
<body>
    
<!-- Navigation -->

<nav class="navbar fixed-top navbar-expand-lg navbar-light bg-light">
  <a class="navbar-brand" href="#">
    <img src="../../../../static/favicon.ico" width="30" height="30" alt="">
    project_name
  </a>
  <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
    <span class="navbar-toggler-icon"></span>
  </button>

  <!-- Everything you want hidden at 940px or less, place within here -->
  <div class="collapse navbar-collapse" id="navbarSupportedContent">
    <ul class="navbar-nav mr-auto">
      
      <li class="nav-item active">
        <a class="nav-link" href="../../../../hello_world.html">home</a>
      </li>
      
      <li class="nav-item active">
        <a class="nav-link" href="https://github.com/theelectricbrain">test</a>
      </li>
      

    </ul>
  </div>
</nav>


    <h2>Welcome to the data folder for the 1 cruise of the Shippy-MacShipface</h2>
    
    <br><h3>Default Icon: </h3><img src="../../../../images/test/something_else.png" class="img-fluid" alt="Default Icon">
    <br><h3>Testing url_for from Template: "Home" = ../../../../hello_world.html</h3>
    <br>
    <h3>
        <a href="../report/index.html">
            Testing url_for from Template: "Report Cruise 1 for Shippy MacShipface"
        </a>
    </h3>
<!-- Footer -->
<div id="footer">
    <div>
        <div><a href="https://github.com/theelectricbrain">Flastik - Copyright 2019</a></div>
    </div>
</div>

    <!-- JQuery -->
    <script type="text/javascript" src="../../../../static/jquery/jquery-3.4.1.min.js"></script>
    <!-- Popper -->
    <script type="text/javascript" src="../../../../static/popper/popper.min.js "></script>
    <!-- Bootstrap  Core JavaScript -->
    <script type="text/javascript" src="../../../../static/js/bootstrap.min.js"></script>
</body>

</html>"""


# Building test web site
def test_build():
    # TODO: add test for rst2html
    # Define Argument parser
    arg_parser = ArgumentParser()
    # - add Builder's arg
    arg_parser = add_Builder_arguments(arg_parser)
    # - add build's arg
    arg_parser = add_build_arguments(arg_parser)
    # - add collect_static_files' arg
    arg_parser = add_collect_static_files_arguments(arg_parser)

    # Parse commend line args.
    # arglist = sys.argv[1:]
    # options = vars(arg_parser.parse_args(args=arglist))

    website = Builder()

    img = Image("Default Icon",
                os.path.join(website.package_path, "base_templates/default_icon.png"),
                dest="test/something_else.png")

    dwnld = Download("README",
                     os.path.join(website.package_path, "README.pdf"))

    @website.route("/hello_world.html")
    def hello_world():
        context['img'] = img
        context['dwnld'] = dwnld
        context['title'] = "Hello World !"
        context['body_text'] = '<h2>Hello World !</h2>'
        pattern = "\n<br><a href='%s/cruise/%s/report/index.html'>%s: report for cruise %s</a>"
        for ship in ship_list:
            cruises = cruise_dict[ship]
            for cruise_id in cruises:
                context['body_text'] += pattern % (ship, cruise_id, ship, cruise_id)
        return render_template('test.html', **context)

    @website.route("/<string:ship>/cruise/<int:cruise_id>/", ship=ship_list, cruise_id=cruise_dict)
    def cruise_report(ship, cruise_id):
        context['dwnld'] = ""
        context['title'] = "%s: Cruise %s" % (ship, cruise_id)
        # Testing "url_for" call from view
        context['navbar_links'][0]['url'] = website.url_for('hello_world')
        context['body_text'] = '<h2>This cruise %s. Hail to the %s !</h2>' % (cruise_id, ship)
        return render_template('test.html', **context)

    @website.route("/<string:ship>/cruise/<int:cruise_id>/<string:folder_name>/",
                   ship=ship_list, cruise_id=cruise_dict, folder_name=['data', 'report'])
    def cruise_n_data(ship, cruise_id, folder_name):
        context['dwnld'] = ""
        context['title'] = "%s - %s" % (folder_name, ship)
        # Testing "url_for" call from view
        context['navbar_links'][0]['url'] = website.url_for('hello_world')
        context['body_text'] = "<h2>Welcome to the %s folder for the %s cruise of the %s</h2>" % (
            folder_name, cruise_id, ship)
        return render_template('test.html', **context)

    website.build(dest=dest)
    collect_static_files()


# Tests based on the html so generated
def test_hello_world():
    with open(os.path.join(dest, "hello_world.html"), "r") as f:
        hello_world_html = f.read()
    assert(hello_world_html == hello_world_str)


def test_cruise_report():
    with open(os.path.join(
            dest, ship_list[0], "cruise", str(cruise_dict[ship_list[0]][0]),
            "index.html"), "r") as f:
        cruise_html = f.read()
    assert(cruise_html == cruise_str)


def test_cruise_n_data():
    with open(os.path.join(
            dest, ship_list[0], "cruise", str(cruise_dict[ship_list[0]][0]),
            "data", "index.html"
    ), "r") as f:
        cruise_n_data_html = f.read()
    assert(cruise_n_data_html == cruise_n_data_str)


# Testing excepted static file locations
def test_static():
    assert(os.path.exists(os.path.join(dest, "static", "stylesheet.css")))
    assert (os.path.exists(os.path.join(dest, "static", "favicon.ico")))
    assert (os.path.exists(os.path.join(dest, "static", "css", "bootstrap.min.css")))
    assert (os.path.exists(os.path.join(dest, "static", "jquery", "jquery-3.4.1.min.js")))
    assert (os.path.exists(os.path.join(dest, "static", "js", "bootstrap.min.js")))
    assert (os.path.exists(os.path.join(dest, "static", "popper", "popper.min.js")))


def test_images():
    assert(os.path.exists(os.path.join(dest, "images", "test", "something_else.png")))


def test_downloads():
    assert(os.path.exists(os.path.join(dest, "downloads", "README.pdf")))
    # Keep that at the end
    shutil.rmtree(dest)









