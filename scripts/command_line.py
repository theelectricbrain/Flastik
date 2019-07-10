#!/usr/bin/env python
import os
import sys
import shutil
import logging
from argparse import ArgumentParser
import flastik
from inspect import getmembers, isfunction, isclass

# Standard logging
log = logging.getLogger(__name__)


def main(args=None):
    """The main routine."""
    if args is None:
        args = sys.argv[1:]
    log.debug("Args: ", args)

    arg_parser = ArgumentParser()
    # Create line command: flastik create_project NAME => creates standard project structure
    arg_parser.add_argument("--create_project", dest="project",
                            type=str, nargs='?', default=False,
                            help="Create a new static website folder project "
                                 "with Flastik.\nSpecify your project name "
                                 "after the option tag.")
    # Create line command: flastik create_doc => create website with documentation
    arg_parser.add_argument("--create_doc", dest="create_doc",
                            action="store_true",
                            help="Create the Flastik documentation locally.")
    arglist = sys.argv[1:]
    options = arg_parser.parse_args(args=arglist)

    if options.project:
        project_path = os.path.join(os.getcwd(), options.project)
        build_project_folder(project_path)

    if options.create_doc:
        doc_path = os.path.join(os.getcwd(), "flastik_documentation")
        build_doc(doc_path)


def build_project_folder(project_path):
    # TODO
    log.debug("project_path: %s", project_path)
    os.makedirs(project_path)
    # Copy templates
    package_path = os.path.abspath(
        os.path.join(os.path.abspath(flastik.__file__), ".."))
    orig = os.path.join(package_path, 'base_templates')
    dest = os.path.join(project_path, 'base_templates')
    shutil.copytree(orig, dest)
    # Create builder script from template
    file_name = os.path.basename(project_path) + ".py"
    with open(os.path.join(project_path, file_name), 'w') as f:
        f.write(builder_template)


def build_doc(doc_path):
    # TODO
    log.debug("doc_path: %s", doc_path)
    os.makedirs(doc_path)
    # Crawling Package for docstrings
    package_path = os.path.abspath(
        os.path.join(os.path.abspath(flastik.__file__), ".."))
    functions = {}
    for f in [ii for ii in getmembers(flastik, isfunction) if 'flastik' is ii[1].__module__]:
        if f[1].__doc__:
            functions[f[0]] = f[1].__doc__.replace("<", "&lt;").replace(">", "&gt;")

    classes = {}
    for c in [ii for ii in getmembers(flastik, isclass) if 'flastik' is ii[1].__module__]:
        classes[c[0]] = {'doc': None}
        # List methods
        classes[c[0]]['methods'] = {}
        for m in [ii for ii in getmembers(c[1], isfunction)]:
            if "__init__" == m[0]:
                classes[c[0]]['doc'] = m[1].__doc__.replace("<", "&lt;").replace(">", "&gt;")
            elif "_" == m[0][0]:
                continue
            else:
                classes[c[0]]['methods'][m[0]] = m[1].__doc__.replace("<", "&lt;").replace(">", "&gt;")
        # List properties
        classes[c[0]]['properties'] = {}
        for p in getmembers(c[1], lambda o: isinstance(o, property)):
            classes[c[0]]['properties'][p[0]] = p[1].__doc__.replace("<", "&lt;").replace(">", "&gt;")



    # TODO: views: home, class_list, class, function_list,
    #  function
    website = flastik.Builder(templates=os.path.join(package_path, 'doc_templates'))

    # Common context
    context = {
        'project_name': 'Flastik',
        'project_url': "https://github.com/theelectricbrain",
        'footer_link': {'name': 'Flastik - Copyright 2019', 'url': 'https://github.com/theelectricbrain'},
    }

    # Views
    @website.route("/flastik.html")
    def home_page():
        context['title'] = "Flastik's Home Page"
        context['title_text'] = "Flastik"
        context['sub_title'] = "A tiny-framework for static website design"
        context['readme'] = flastik.Download(
            "Read Me", os.path.join(website.package_path, "README.pdf"))
        context['intro'] = (
            "Flastik is a tiny-framework for static website design inspired "
            "by Flask micro-framework (see http://flask.pocoo.org/docs/1.0/). "
            "It provides tools for designing simple static website project "
            "using Flask-like syntax and project architecture as well as "
            "leveraging Jinja2 templating system and Bootstrap 'beautyfying' "
            "capability. Additionally, Flastik aims to easy the porting to "
            "Flask if extra functionality becomes needed further down your "
            "website life cycle. Basic knowledge of Jinja2 templating and "
            "Flask1.0 microwebframework will be assumed from here on "
            "(see http://flask.pocoo.org/docs/1.0/ and "
            "http://jinja.pocoo.org/docs/2.10/). <br><br>In addition classes "
            "and functions have been designed in order to ease the management "
            "and templating of images, downloads and other static files "
            "(see StaticFile, Image and Download classes as well as "
            "collect_static_files function).")
        return flastik.render_template("home_page.html", **context)

    @website.route("/classes/")
    def classes_page():
        context['title'] = "Flastik's Classes"
        context['classes'] = classes
        return flastik.render_template("classes_page.html", **context)

    @website.route("/functions/")
    def functions_page():
        context['title'] = "Flastik's Functions"
        context['functions'] = functions
        return flastik.render_template("functions_page.html", **context)


    website.build(dest=doc_path)
    # collect_static_files()


builder_template = """
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

if __name__ == "__main__":
    # Define Argument parser
    arg_parser = ArgumentParser()
    # - add Builder's arg
    arg_parser = add_Builder_arguments(arg_parser)
    # - add build's arg
    arg_parser = add_build_arguments(arg_parser)
    # - add collect_static_files' arg
    arg_parser = add_collect_static_files_arguments(arg_parser)

    # Parse commend line args.
    arglist = sys.argv[1:]
    options = vars(arg_parser.parse_args(args=arglist))

    # Initiate Builder
    website = Builder()

    # Common context
    context = dict(
        project_name=os.path.basename(os.getcwd()),
        footer_link={
            'name': 'Flastik - Copyright 2019',
            'url': 'https://github.com/theelectricbrain'},
    )


    # Some static files
    img = Image("Default Icon",
                os.path.join(website.package_path, "base_templates/default_icon.png"),
                dest="test/something_else.png")

    dwnld = Download("READ ME",
                     os.path.join(website.package_path, "README.pdf"))


    # Views
    @website.route("/hello_world.html")
    def hello_world():
        # context
        context['navbar_links'] = [
            {'name': 'home', 'url': website.url_for('hello_world')},
            {'name': 'test', 'url': 'https://github.com/theelectricbrain'},]
        context['img'] = img
        context['dwnld'] = dwnld
        context['title'] = "Hello World !"
        context['body_text'] = 'Hello World !'
        return render_template('hello_world.html', **context)


    website.build()
    collect_static_files()       
"""

if __name__ == "__main__":
    main()

