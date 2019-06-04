#!/usr/bin/env python
# TODO: define copyright/license
"""
Flastic - A Flask-like pico-framework for static websites.
(c) Copyright 2019. All Rights Reserved. See LICENSE for details.
"""

import os
import re
import sys
import shutil
import logging
import traceback
from functools import wraps
import itertools
from jinja2 import Environment, ChoiceLoader, FileSystemLoader
from jinja2 import select_autoescape
from uuid import uuid4

# Standard logging
log = logging.getLogger(__name__)

# TODO: docs
# TODO: test units
# TODO: review log scheme and levels
# TODO: add log.error to raise Exception blocks
# TODO: dev. argparsers for Builder, and collect_static_files
# TODO: replace flastic by flastik
# TODO: redo as an example this file:///net/moli.local/export/ipu1/uhdas_data_archive/pelican/PE19_13_Sidorovskaia/reports/index.html
#       by Monday.
# TODO: redo README.pdf


class Builder:
    # Tracking page being rendered
    current_route = None
    # instance tracker
    instance = []
    # Container for web page = view + var(s) + route pattern + key args. + html name
    web_pages = {}
    routes = []

    def __init__(self, templates=None, use_package_templates=True,
                 bootstrap_folder=None, css_style_sheet=None,
                 favicon=None, meta={}, description=None, author=None,
                 log_level='ERROR'):
        """
        Pico-framework designed to be used like the App Class of Flask.
        Defines the overall project environment as well as provides functions,
        methods and decorators for templating, routing and building static
        websites.

        Keyword Args:
            templates: path to template folder, str.
                Your templates are added to the "base templates" provided in
                the package (see README.pdf)

            use_package_templates: boolean switch, bool.
                If True (default): "base templates" will be available in
                    the template environment.
                If False: they won't.

            bootstrap_folder: path to bootstrap folder, str.
                If None (default): a complete distribution of Bootstrap 2.3.2
                    will be used and copied in static_website_root/static at
                    built/deployment
                Otherwise: specified will be used and linked to

            css_style_sheet: path to *.css stylesheet file, str.
                If None (default): a blank stylesheet will be provided, used
                    and copied in static_website_root/static at built/deployment
                Otherwise: specified will be used and linked to

            favicon: path to web browser tab icon, str.
                if None (default): a generic python icon will be used and
                    copied in static_website_root/static at built/deployment
                Otherwise: specified will be used and copied to static

            meta: dictionary providing meta information, dict.

            description: web site's description (meta info.), str.

            author: web site's author(s) (meta info.), str.

            log_level: logging level, str. ('CRITICAL', 'ERROR', 'WARNING',
                'INFO' or 'DEBUG')
        """
        # Environment
        # - Logging scheme
        try:
            log.setLevel(log_level)
        except ValueError:
            msg = "%s is not a valid log_level." % log_level
            msg += "\nMust be CRITICAL, ERROR, WARNING, INFO or DEBUG"
            log.error(msg)
            raise Exception(msg)
        log_handler = logging.FileHandler('flastic_%s.log' % log_level)
        log.addHandler(log_handler)
        if log.level <= 20:
            log.addHandler(logging.StreamHandler(sys.stdout))
        log_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        # - Check: only one instance per project
        if not self.instance:
            self.instance.append(self)
        else:
            msg = "only one instance of Builder can be created per project."
            log.error(msg)
            raise Exception(msg)
        # - Backend attributes
        self.meta = meta
        self.favicon = favicon
        self.bootstrap_folder = bootstrap_folder
        self.copy_bootstrap = False
        self.css_style_sheet = css_style_sheet
        self.copy_css = False
        self.dest = None
        self.static_path = None
        self.package_path = os.path.dirname(os.path.abspath(__file__))
        if description:
            self.meta['description'] = description
        if author:
            self.meta['author'] = author
        # - Template loader
        standard_templates_path = os.path.join(os.getcwd(), 'templates/')
        custom_loader = None
        loader = None
        #  * custom templates
        if templates:
            if os.path.isdir(templates):
                log.info("Using specified template folder: %s" % templates)
                custom_loader = FileSystemLoader(templates)
            else:
                msg = "Invalid path to templates: %s" % templates
                log.error(msg)
                raise Exception(msg)
        elif not templates and os.path.isdir(standard_templates_path):
            log.info("Using standard template folder: %s" % standard_templates_path)
            custom_loader = FileSystemLoader(standard_templates_path)
        if not use_package_templates and not custom_loader:
            msg = """No templates were found.
            Either set use_package_templates=True
            or specify templates='/path/to/your/templates/"""
            log.error(msg)
            raise Exception(msg)
        #  * package Templates
        # Note: if same name, user template override package template
        if use_package_templates:
            package_loader = FileSystemLoader(
                os.path.join(self.package_path, 'base_templates'))
            if custom_loader:
                log.info("Using both package & specified template folders")
                loader = ChoiceLoader([custom_loader, package_loader])
            else:
                log.info("Using package template folder only")
                loader = package_loader
        else:
            log.info("Using specified template folder only")
            loader = custom_loader
        #  * sanity check
        if loader is None:
            msg = """No templates where found for this project.
            Use default option 'use_package_templates=True'
            Or/and provide a valid path to templates via the 'templates' option."""
            log.error(msg)
            raise Exception(msg)
        self.jinja_env = Environment(
            loader=loader,
            # Note: autoescape stops you from injecting str into template
            #       as in the html_image method for instance
            # autoescape=select_autoescape(['html', 'xml'])
        )
        # - Environment variables
        self.jinja_env.globals['meta'] = self.meta
        # - Environment methods
        self.jinja_env.globals['url_for'] = self.url_for
        # - Provide Bootstrap Yes/No
        if self.bootstrap_folder is None:
            self.copy_bootstrap = True
            self.bootstrap_folder = os.path.join(
                self.package_path, 'bootstrap')
        # Provide Css Style Sheet Yes/No
        if self.css_style_sheet is None:
            self.copy_css = True
            self.css_style_sheet = os.path.join(
                self.package_path, 'base_templates/stylesheet.css')
        # Provide favicon Yes/No
        if self.favicon is None:
            self.favicon = os.path.join(
                self.package_path, 'base_templates/default_icon.png')

    def route(self, route, _func=None, **kwargs_deco):
        """
        Inspired by “@app.route” Flask decorator, @website.route decorator
        is an elegant way to specify which *.html file(s) will be created
        and where should it (they) go.

            Note: see README.pdf provided in package for more details

        Args:
            route: Url/Route pattern, str.
                Ex.: "/what/ever/route/<type:var1>/.../<type:varN>/...",
                where the different variable types available are:
                    string	accepts any text without a slash (the default)
                    int	    accepts integers
                    float	like int but for floating point values
                    path	like the default but also accepts slashes
                See README.pdf for more details.

        Keyword Args:
            _func: wrapped python func
            **kwargs_deco: list(s) of values or list(s) of lists corresponding
                to the variable(s) specified in the Route Pattern
        """
        # Note: boiler plate inspired by
        #       https://realpython.com/primer-on-python-decorators/#more-real-world-examples
        log.debug("route: %s" % route)
        log.debug("deco kwargs: %s" % kwargs_deco)
        # Regular expression for generic <type:var>
        reg_expr = r"<\s*?(\b\w+\b)\s*?:\s*?(\b\w+\b)\s*?>"
        # Separate HTML file name from route
        html_name = "index.html"
        if ".html" in route.split("/")[-1]:
            html_name = route.split("/")[-1]
            # - making sure there is no logic in the html_name
            if re.match(reg_expr, html_name):
                msg = "Logic cannot be used in html file names in Flastic projects."
                msg += "\nIt is unfortunate but it is what it is, please change '%s'" % html_name
                log.error(msg)
                raise Exception(msg)
            route = route.replace(html_name, '')
        # Generate routes and associated iterator
        # - base route
        route_pattern = re.sub(reg_expr, "%s", route)
        if route_pattern[0] == '/':  # remove leading '/'...collide with os.path.join
            route_pattern = route_pattern[1:]
        # - variables matches type (if any)
        found = re.findall(reg_expr, route)
        log.debug("Found Var.: %s" % found)
        # - sanity checks:
        key_args = list(kwargs_deco.keys())
        if len(found) is not len(key_args):
            raise Exception("Number of key variables does not match the number"
                            " of variables specified in the route: %s" % route)
        # - check if names are similar between route and kwargs_deco
        if not [t[1] for t in found] == key_args:
            raise Exception("There is a mismatch in the naming or the order "
                            "between the kwargs and the variables specify "
                            "in %s" % route)
        # - generate list of route variables
        route_vars = []
        if found:
            route_vars = self._generate_route_vars(found, kwargs_deco, route)
            log.debug("Route: %s; Vars.: %s" % (route_pattern, route_vars))
        # - check if routes already in use, if not store them
        for vv in route_vars:
            new_route = route_pattern % vv
            log.debug(new_route)
            # - check if route is url and system file friendly
            check_url_for_unsafe_characters(new_route)
            check_path_for_illegal_characters(new_route)
            if new_route not in self.routes:
                self.routes.append(new_route)
                log.info("New route: %s" % new_route)
            else:
                raise Exception("Change route pattern and/or variables: "
                                "%s already used by another view" % new_route)

        def wrapper(func):
            @wraps(func)
            def wrapped_func(*args, **kwargs):
                if args:
                    log.debug("*args: %s" % list(args))
                if kwargs:
                    log.debug("**kwargs: %s" % list(kwargs))
                # Sanity checks:
                # - make sure the view is not called 'static'
                if func.__name__ == 'static':
                    raise Exception("view function cannot be named 'static'. "
                                    "This name is reserved for the jinja environment.")
                # - check if corresponding amount of variables
                if not len(key_args) == len(args):
                    raise Exception(
                        "Number of variables in %s does not match the number "
                        "of variables specified in the route" % func.__name__)
                # FIXME: Check if names are matching between kwargs_deco and args
                #        Dunno how to do that !? Don't think it is possible !
                # if not key_args == list(args):
                #     raise Exception(
                #         "Variable names in %s's definition does not match the "
                #         "variable names in the route" % func.__name__)

                # Standard decorator return
                return func(*args, **kwargs)

            # Store function in Builder
            if func.__name__ in self.web_pages.keys():
                raise Exception("'%s' is already used for another view "
                                % func.__name__)
            self.web_pages[func.__name__] = {
                'route_pattern': route_pattern,
                'html_name': html_name,
                'key_args': key_args,
                'route_vars': route_vars,
                'view': func}
            log.debug("Storing %s view parameters: /n%s" % (
                func.__name__, self.web_pages[func.__name__]))
            return wrapped_func

        # Mechanism for handling decorator args & kwargs
        # FIXME: not sure whether I need this original block !?
        # if _func is None:
        #     return wrapper
        # else:
        #     return wrapper(_func)
        return wrapper

    def url_for(self, name, **kwargs):
        """
        Flask-lookalike templating function.
        Return relative path to requested *.html file or static file

        Args:
            name: view name or 'static', str.

        Keyword Args:
            **kwargs: view arguments as kwargs or 'filename' for static files.

        Notes:
         - order of the **kwargs needs to match the order of the view's args.
         - url_for can be used inside both templates and views

        Returns: relative path, str.
        """
        key_args = list(kwargs.keys())
        # Static
        if name == 'static':
            # search for static file
            if not 'filename' in key_args:
                raise Exception("'filename' needs to be specify when using "
                                "'static' in url_for")
            path = os.path.join('static', kwargs['filename'])  # for now
        # Views
        elif name in self.web_pages.keys():
            # get url for that particular view
            # - checking key args
            orig_key_args = self.web_pages[name]['key_args']
            if not key_args == orig_key_args:
                msg = """Error: key args need to match "%s"'s original key_args.""" % name
                msg += "\nOrig.: %s\nGiven: %s" % (orig_key_args, key_args)
                raise Exception(msg)
            path = self.web_pages[name]['route_pattern'] % tuple(kwargs.values())
            path = os.path.join(path, self.web_pages[name]['html_name'])
        else:
            log.error("'%s' does not have a url_for" % name)
            # TODO: Do I wan to raise here and make it less permissive
            return None
        # - make relative path to where it got called
        log.debug("current route: %s " % self.current_route)
        relative_path = os.path.relpath(path, self.current_route)
        log.debug("relative path: %s" % relative_path)
        return relative_path

    def build(self, dest=None, views=[], overwrite=True,
              static_umask=0o655, html_umask=0o644, dir_umask=0o751):
        """
        Build and deploy the static website project, that is:
         - Make web site folder tree (to destination if specified)
         - Copy Bootstrap Suite if needed (i.e. bootstrap, java scripts, css)
         - Render Templates and make *.html files
         - Apply u-masks to directories and files

        Keyword Args:
            dest: path to deployment destination, str.
                If None (default): the web site will be built in "./build"

            views: list of views to be built, [str.,...,str.]
                Note: All views are built by default.

            overwrite: boolean switch, bool.
                If True (default): pre-existing *.html files and Bootstrap
                    suite will be overwritten.

            static_umask: U-mask for Bootstrap suite, U-mask code
                Default value: 0o655

            html_umask: U-mask for *.html files, U-mask code
                Default value: 0o644

            dir_umask: U-mask for directories, U-mask code
                Default value: 0o751

        """
        # New attributes...not compliant with PEP but whatever
        self.overwrite = overwrite
        self.static_umask = static_umask
        self.html_umask = html_umask
        self.dir_umask = dir_umask
        # Sanity checks
        if dest is None:
            self.dest = os.path.join(os.getcwd(), 'build')
        else:
            if os.path.isdir(dest):
                self.dest = dest
            else:
                raise Exception("the provided destination does not exist: %s"
                                % dest)
        log.debug("Website destination: %s" % self.dest)
        if not type(views) == list:
            views = [views]
        if not views:
            views = self.web_pages.keys()
        # Building static website:
        # - Make website dirs
        # IMPROVE_ME: add progress bar here
        for name in views:
            route_pattern = self.web_pages[name]['route_pattern']
            route_vars = self.web_pages[name]['route_vars']
            if not route_vars:
                full_paths = [os.path.join(self.dest, route_pattern)]
            else:
                full_paths = []
                for vv in route_vars:
                    full_paths.append(
                        os.path.join(self.dest, route_pattern % vv))
            for full_path in full_paths:
                if not os.path.exists(full_path):
                    os.makedirs(full_path, self.dir_umask)
                    log.debug("Making %s" % full_path)
        # - Make 'static' folder & move static files where they belong
        self.static_path = os.path.join(self.dest, 'static')
        if not os.path.exists(self.static_path):
            os.makedirs(self.static_path)
            log.debug("Making %s" % self.static_path)
        # - Copy bootstrap & custom CSS style sheet
        if self.copy_bootstrap:
            for ff in os.listdir(self.bootstrap_folder):
                orig = os.path.join(self.bootstrap_folder, ff)
                dest = os.path.join(self.static_path, ff)
                if os.path.isfile(orig):
                    if os.path.exists(dest) and not self.overwrite:
                        continue
                    else:
                        shutil.copy(orig, dest)
                        log.debug("Copying %s to %s" % (orig, dest))
                elif os.path.isdir(orig):
                    try:
                        shutil.copytree(orig, dest)
                    except FileExistsError as err:
                        if self.overwrite:  # force overwriting
                            shutil.rmtree(dest)
                            shutil.copytree(orig, dest)
                            log.debug("Copying %s to %s" % (orig, dest))
                        else:
                            raise err
        # - Copy CSS style sheet
        if self.copy_bootstrap:
            dest = os.path.join(self.static_path, 'stylesheet.css')
            if os.path.exists(dest) and not self.overwrite:
                pass
            else:
                shutil.copy(self.css_style_sheet, dest)
                log.debug("Copying %s to %s" % (self.css_style_sheet, dest))
                self.css_style_sheet = dest
        # - Copy favicon.ico
        dest = os.path.join(self.static_path, 'favicon.ico')
        if os.path.exists(dest) and not self.overwrite:
            pass
        else:
            shutil.copy(self.favicon, dest)
            log.debug("Copying %s to %s" % (self.favicon, dest))
            self.favicon = dest

        # - Apply umasks to static
        apply_umasks(self.static_path, self.dir_umask, self.static_umask)

        # - Render Templates
        # IMPROVE_ME: add progress bar here
        for name in views:
            route_pattern = self.web_pages[name]['route_pattern']
            route_vars = self.web_pages[name]['route_vars']
            html_name = self.web_pages[name]['html_name']
            view = self.web_pages[name]['view']
            if not route_vars:
                #  * inform current page being renderer (for url_for purposes)
                route = route_pattern
                self.current_route = route
                #  * then render
                rendered_html = view()
                #  * finally write to html file
                log.info("Writting %s at %s/%s" % (html_name, self.dest, route))
                self._write_html_file(html_name, route, rendered_html)
            else:
                for vv in route_vars:
                    #  * inform current page being renderer (for url_for purposes)
                    route = route_pattern % vv
                    self.current_route = route
                    #  * then render
                    rendered_html = view(*vv)
                    #  * finally write to html file
                    log.info("Writting %s at %s/%s" % (html_name, self.dest, route))
                    self._write_html_file(html_name, route, rendered_html)

    # Static Methods
    @staticmethod
    def check_vars_vs_type(var_type, var_name, var_val, route):
        """
        Check if the variable(s) specified in @Builder.route(...) complies(y)
        to the framework's requirements. That is:
         - Is the variable a list of values or a list of lists?
         - Are the values every lists of the same type?

        Args:
            var_type: type of values, str. in ["string", "int", "float", "path"]
            var_name: variable name, str.
            var_val: list of ; list
            route: route pattern, str.

        Returns: sanitized var_val

        """
        # Checking uniformity
        types = set([type(n) for n in var_val])
        if len(types) is not 1:
            msg = """
            Error type in %s list.
            Only list of uniform values or list of lists are supported.\n
            E.g. route: %s; types: %s""" % (
                var_name, route, [str(type(vv)) for vv in var_val])
            raise Exception(msg)

        if list not in types:
            if var_type == "string" and not all(isinstance(n, str) for n in var_val):
                raise Exception("Error type in %s values. "
                                "'string' type only valid for list of str."
                                "\nE.g. route: %s" % (var_name, route))
            elif var_type == "int" and not all(isinstance(n, int) for n in var_val):
                raise Exception("Error type in %s values. "
                                "'int' type only valid for list of int."
                                "\nE.g. route: %s" % (var_name, route))
            elif var_type == "float" and not all(isinstance(n, float) for n in var_val):
                raise Exception("Error type in %s values. "
                                "'float' type only valid for list of floats."
                                "\nE.g. route: %s" % (var_name, route))
            # FIXME: not sure if I need that check !?
            elif var_type == "path" and not all(os.path.exists(n) for n in var_val):
                raise Exception("Error in %s values. "
                                "Some of those paths do not exist."
                                "\nE.g. route: %s" % (var_name, route))
            elif var_type not in ["string", "int", "float", "path"]:
                raise Exception("'%s' type in %s is not supported. "
                                "Available types: string, int, float, path. "
                                "\nE.g. route: %s" %
                                (var_type, var_name, route))
            else:
                # - Trimming white spaces beforehand
                if var_type in ["string", "path"]:
                    var_val = list(map(str.strip, var_val))
        return var_val

    # Hidden Methods
    def _generate_route_vars(self, found, kwargs_deco, route):
        """
        Generate the variables associated with a routing pattern.
        It also check the sanity of these so generated variables, such as:
         - Do the variables have the expected type?
         - Does the number of variables corresponds to the routing pattern and
           the folder ramification?

        Args:
            found: RegEx groups
            kwargs_deco: dictionary of key arguments, dict.
            route: routing pattern, str.

        Returns: list of tuples
        """
        var_lists = []
        route_vars = []
        all_strings = True
        # Checking list of values and list of lists
        for group in found:
            values = kwargs_deco[group[1]]
            # - check if first container is a list
            if not isinstance(values, list):
                raise Exception("Error type: %s variable must be a list" % group[1])
            var_type = group[0]
            var_name = group[1]
            # - check if dealing with a list of lists
            if all(isinstance(n, list) for n in values):
                all_strings = False
                clean_list = []
                self.check_vars_vs_type(var_type, var_name, values, route)
                for ll in values:
                    var_val = self.check_vars_vs_type(var_type, var_name, ll, route)
                    clean_list.append(var_val)
                var_lists.append(clean_list)
            else:
                var_val = self.check_vars_vs_type(var_type, var_name, values, route)
                var_lists.append(var_val)
        log.debug("Var list: %s" % var_lists)
        # Generate list of route variables
        # - if dealing with a list of strings only
        if all_strings:
            route_vars = list(itertools.product(*var_lists))
        # - otherwise
        else:
            for l, group in zip(var_lists, found):
                var_name = group[1]
                #  * first time around
                if not route_vars:
                    if all(isinstance(vv, list) for vv in l):  # List of list
                        for lv in l:
                            route_vars.extend([[vv] for vv in lv])
                    else:  # List of values
                        route_vars = [[vv] for vv in l]
                    required_length = len(route_vars)
                #  * next time around
                else:
                    # FIXME: Not sure which behavior is the best, either:
                    #         - always match the number routes made so far
                    #         - or to the length of last list of value
                    #         - or combination...!?
                    #        There are no good or bad answer here yet it would
                    #        fundamentally change the behavior here.
                    #         See 'Scheme#'
                    old_route_vars = route_vars.copy()
                    route_vars = []
                    if all(isinstance(vv, list) for vv in l):  # List of list
                        if len(l) is not required_length:  # Sanity check
                            raise Exception(
                                "'%s' requires %s lists." % (var_name, required_length))
                        for rr, lv in zip(old_route_vars, l):
                            for vv in lv:
                                route_vars.append(rr + [vv])
                        # Scheme1 - depending on previous:
                        # - Requirement based on "number routes made so far"
                        # required_length = len(route_vars)
                    else:  # List of values
                        for rr in old_route_vars:
                            for vv in l:
                                route_vars.append(rr + [vv])
                        # Scheme1 - depending on previous:
                        # - Requirement based on "number values in list"
                        # required_length = len(l)
                    # Scheme2 - always match number of existing routes:
                    required_length = len(route_vars)
            #  * turn inside lists into tuples
            route_vars = [tuple(lv) for lv in route_vars]
        return route_vars

    def _write_html_file(self, html_name, route, rendered_html):
        """
        Write rendered html to file

        Args:
            html_name: file name, str.
            route: path to file, str.
            rendered_html: rendered html, str.
        """
        # Put path together
        html_path = os.path.join(
            self.dest, route, html_name)
        # Overwrite check
        if os.path.exists(html_path) and not self.overwrite:
            return
        # Write html file
        with open(html_path, "w") as f:
            f.write(rendered_html)
        #  * change permission
        os.chmod(html_path, self.html_umask)


# Misc library
def check_url_for_unsafe_characters(url):
    unsafe = ['"', '<', '>', '#', '%', '{', '}', '|', '^', '~', '[', ']', '`', ' ']
    for cc in url:
        if cc in unsafe:
            raise Exception(
                "%s is an unsafe url.\n'%s' should not be used." % (url, cc))


def check_path_for_illegal_characters(path):
    unsafe = ['.', '"', '[', ']', ':', ';', '|', '=', ' ', '?', '$']
    for cc in path:
        if cc in unsafe:
            raise Exception(
                "%s is an illegal path.\n'%s' should not be used." % (path, cc))


def apply_umasks(path, dir_umask, file_umask):
    for root, dirs, files in os.walk(path):
        for d in dirs:
            os.chmod(os.path.join(root, d), dir_umask)
        for f in files:
            os.chmod(os.path.join(root, f), file_umask)


# Flask-lookalikes Library
def render_template(template_name, **context):
    """
    Flask-lookalike templating function.
    Args:
        template_name:
        **context:

    Returns:

    """
    # Fetch existing Builder instance
    if not Builder.instance:
        msg = """"
        A flastic.Builder instance must be created beforehand in order to use 
        'render_template'."""
        raise Exception(msg)
    else:
        jinja_env = Builder.instance[0].jinja_env
    # Get template through jinja template env/loader
    template = jinja_env.get_template(template_name)
    return template.render(**context)
    # print(template.render(**context))


# Library for "static files"...as in other files than html and bootstrap related
class StaticFile:
    # Storage container for aggregating static file info
    storage = {'name': [], 'type': [], 'source': [], 'destination': []}

    def __init__(self, name, source, dest=None, handle_duplicate=False):
        """
        Dedicated Python class for static files
          Note: this class keeps track of of all of its instances.

        Args:
            name: display name, str.
            source: path to source, str.

        Keyword Args:
            dest: path to destination, str.
              File will be copied to os.path.join('website_root/files/', dest)
            handle_duplicate: boolean switch, bool.
              If True: the class will automatically take care of duplicated
                destinations.
              If False (default): file destination must be unique or it will
                raise an error
        """
        # Sanity check
        source = os.path.abspath(source)
        if not os.path.isfile(source):
            raise Exception("%s either does not exist or is not a file." % source)
        # Attributes
        self.builder = None
        self.name = name
        self.source = source
        # Note: following line will be overwritten in subclasses
        self.type = 'files'
        # Fetch existing Builder instance
        self.builder = None
        if Builder.instance:
            self.builder = Builder.instance[0]
        # File Management Strategy
        # - define destination
        if not dest:
            filename = os.path.basename(source)
        elif os.path.splitext(dest)[-1]:  # is the file name specified in dest?
            # sanity check
            if not os.path.splitext(dest)[-1] == os.path.splitext(source)[-1]:
                raise Exception("Source and destination must have the same "
                                "extension: %s ~= %s" % (source, dest))
            filename = dest
        else:
            filename = os.path.join(dest, os.path.basename(source))
        # - some formatting
        if filename[0] == '/':
            filename = filename[1:]
        log.info("File Name/Destination: %s" % filename)
        # - checking for duplicates
        if filename not in self.storage['destination']:
            self.destination = filename
        else:
            if handle_duplicate:  # define unique subfolder
                self.destination = os.path.join(uuid4(), filename)
            else:
                raise Exception(
                    "%s is already in use. Change source name or destination "
                    "using the 'dest' option" % filename)
        log.info("Destination: %s" % self.destination)
        # - aggregating static file info
        self.storage['name'].append(name)
        self.storage['source'].append(source)
        self.storage['destination'].append(self.destination)
        # Note: following line will be overwritten in subclasses
        self.storage['type'].append(self.type)

    @property
    def url(self, current_route=None):
        """
        Return relative path to file during template rendering

        Keyword Args:
            current_route: path to *.html being built, str.

        Returns: relative path, str.
        """
        # Check point: in case this method/class is used outside of
        #              a flastic projects
        if not self.builder and not current_route:
            msg = """
            A flastic.Builder instance must be created beforehand in order to 
            use the any Static class.Otherwise you need to re-write your 
            template and specify the 'current_route' option for each 'url' 
            method's call."""
            raise Exception(msg)
        # - make relative path to where it got called
        dest = os.path.join(self.type, self.destination)
        relative_path = os.path.relpath(dest, self.builder.current_route)
        log.debug("staticfile relative path: %s" % relative_path)
        return relative_path


class Image(StaticFile):
    def __init__(self, name, source, dest=None, handle_duplicate=False):
        """
        Dedicated Python class for image static files
          Note: this class keeps track of of all of its instances.

        Args:
            name: display name, str.
            source: path to source, str.

        Keyword Args:
            dest: path to destination, str.
              File will be copied to os.path.join('website_root/images/', dest)
            handle_duplicate: boolean switch, bool.
              If True: the class will automatically take care of duplicated
                destinations.
              If False (default): file destination must be unique or it will
                raise an error
        """
        super(Image, self).__init__(name, source, dest=dest,
                                    handle_duplicate=handle_duplicate)
        # Overwrite StaticFile attributes so that this type of statics end up
        # in their own folder
        self.type = 'images'
        self.storage['type'][-1] = self.type

    @property
    def html_image(self):
        """Returns html formatted image block"""
        img = '<img src="%s" alt="%s">' % (self.url, self.name)
        log.debug("img: %s" % img)
        return img
    # TODO: add similar templating methods specific to images below


class Download(StaticFile):
    def __init__(self, name, source, dest=None, handle_duplicate=False):
        """
        Dedicated Python class for downloadable static files
          Note: this class keeps track of of all of its instances.

        Args:
            name: display name, str.
            source: path to source, str.

        Keyword Args:
            dest: path to destination, str.
              File will be copied to os.path.join('website_root/downloads/', dest)
            handle_duplicate: boolean switch, bool.
              If True: the class will automatically take care of duplicated
                destinations.
              If False (default): file destination must be unique or it will
                raise an error
        """
        super(Download, self).__init__(name, source, dest=dest,
                                       handle_duplicate=handle_duplicate)
        # Overwrite StaticFile attributes so that this type of statics end up
        # in their own folder
        self.type = 'downloads'
        self.storage['type'][-1] = self.type

    @property
    def html_download(self):
        """Returns html formatted downloadable block"""
        d_link = "<a href='%s' download>%s</a>" % (self.url, self.name)
        log.debug("d_link: %s" % d_link)
        return d_link
    # TODO: add similar templating methods specific to downloads below


def collect_static_files(static_root=None, overwrite=True, copy_locally=False,
                         file_umask=0o644, dir_umask=0o755):
    """
    Collects all StaticFile's (and Child classes') instances and deploy them at
    the web site root directory

    Keyword Args:
        static_root: path to site root directory, str.
        overwrite: boolean switch, bool.
          If True (default): existing static files will be overwritten
          If False: they won't
        copy_locally: boolean switch, bool.
          If True: static files will copied locally
          If False (default): symlinks will be used instead
        file_umask: u-mask for files
        dir_umask: u-mask for directories
    """
    # Fetch existing Builder instance
    if not Builder.instance and not static_root:
        msg = """"
        In order to use this function, one needs to either create a 
        flastic.Builder instance beforehand or specify a deployment 
        destination via the 'dest' option."""
        # TODO: log.error first...everywhere
        raise Exception(msg)
    elif not static_root:  # Note: user specified dest takes over
        static_root = Builder.instance[0].dest

    if not StaticFile.storage:
        print("There is no static files to collect")
        return
    # File Management Strategy
    sources = StaticFile.storage['source']
    destinations = StaticFile.storage['destination']
    types = StaticFile.storage['type']
    # - Make folder architecture
    for src, dst, tp in zip(sources, destinations, types):
        # - making separated folder for Image, Download and StaticFile instances
        dst = os.path.join(static_root, tp, dst)
        dir_name = os.path.dirname(dst)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, dir_umask)
    # - Make symlink to (or copy) source files in their dest. location
    #     Note: symlinks require a certain server/file system set-up
        if os.path.exists(dst) and not overwrite:
            continue
        elif os.path.exists(dst) and overwrite:
            os.remove(dst)
        if not copy_locally:
            os.symlink(src, dst)
        else:
            shutil.copy(src, dst)
            os.chmod(dst, file_umask)


if __name__ == '__main__':
    # TODO: def standard argument parsers for flastik projects
    # Command line arguments to parse per group:
    #  - common: log_level, file_umask, dir_umask
    #  - builder: url_root, templates, bootstrap_folder, css_style_sheet,
    #             use_package_templates, favicon, meta, description=None, author=None
    #  - builder.build: dest, views, overwrite, static_umask, html_umask, dir_umask
    #  - collect_static_files: static_root, overwrite, copy_locally,
    #                          file_umask, dir_umask

    # TODO: def. different handler per log level (console + file or just file)

    # TODO: Turn into Test Unit
    website = Builder(log_level='INFO')

    img = Image("Default Icon",
                os.path.join(website.package_path, "base_templates/default_icon.png"),
                dest="test/something_else.png")

    dwnld = Download("README",
                     os.path.join(website.package_path, "README.pdf"))

    # General context for navbar and footer
    context = {
        'project_name': 'project_name',
        'navbar_links': [
            {'name': 'home', 'url': "?"},
            {'name': 'test', 'url': 'https://www.surfline.com'},
        ],
        'footer_link': {'name': 'Flastic - Copyright 2019', 'url': 'https://www.surfline.com'},
    }

    ship_list = ["Shippy-MacShipface", "Boatty-MacBoatface"]
    cruise_list = [[1, 2], [99, 98, 97]]

    @website.route("/hello_world.html")
    def hello_world():
        context['img'] = img
        context['dwnld'] = dwnld
        context['title'] = "Hello World !"
        context['body_text'] = '<h2>Hello World !</h2>'
        pattern = "\n<br><a href='%s/cruise/%s/report/index.html'>%s: report for cruise %s</a>"
        for ship, cruises in zip(ship_list, cruise_list):
            for cruise_id in cruises:
                context['body_text'] += pattern % (ship, cruise_id, ship, cruise_id)
        return render_template('test.html', **context)

    @website.route("/<string:ship>/cruise/<int:cruise_id>/",
                   ship=ship_list, cruise_id=cruise_list)
    def cruise_report(ship, cruise_id):
        context['dwnld'] = ""
        context['title'] = "%s: Cruise %s" % (ship, cruise_id)
        # Testing "url_for" call from view
        context['navbar_links'][0]['url'] = website.url_for('hello_world')
        context['body_text'] = '<h2>This cruise %s. Hail to the %s !</h2>' % (cruise_id, ship)
        return render_template('test.html', **context)


    @website.route("/<string:ship>/cruise/<int:cruise_id>/<string:folder_name>/",
                   ship=ship_list, cruise_id=cruise_list, folder_name=['data', 'report'])
    def cruise_n_data(ship, cruise_id, folder_name):
        context['dwnld'] = ""
        context['title'] = "%s - %s" % (folder_name, ship)
        # Testing "url_for" call from view
        context['navbar_links'][0]['url'] = website.url_for('hello_world')
        context['body_text'] = "<h2>Welcome to the %s folder for the %s cruise of the %s</h2>" % (
            folder_name, cruise_id, ship)
        return render_template('test.html', **context)

    website.build()
    collect_static_files()


    # TODO: make test based on the html so generated
    # TODO: make test on excepted static file locations
