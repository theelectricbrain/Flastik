#!/usr/bin/env python
import os
import re
import sys
import shutil
import logging
from functools import wraps
import itertools
from jinja2 import (Environment, ChoiceLoader, FileSystemLoader,
                    select_autoescape)
from uuid import uuid4

# Standard logging
log = logging.getLogger(__name__)

# TODO: docs
# TODO: test units


class Builder:
    """...a little bit like the App class of Flask"""
    # Tracking page being rendered
    current_route = None
    # instance tracker
    instance = []
    # Container for web page = view + var(s) + route pattern + html name
    web_pages = {}
    routes = []

    def __init__(self, url_root,
                 templates=None,
                 bootstrap_folder=None,
                 css_style_sheet=None,
                 use_package_templates=True,
                 favicon=None, meta=None):
        # Environment
        # - Check: only one instance per project
        if not self.instance:
            self.instance.append(self)
        else:
            raise Exception("only one instance of Builder can be created per "
                            "project.")
        # - Backend attributes
        self.url_root = url_root
        self.bootstrap_folder = bootstrap_folder
        self.copy_bootstrap = False
        self.css_style_sheet = css_style_sheet
        self.copy_css = False
        self.dest = None
        self.static_path = None
        # TODO: self.meta = {"description": "blabla", "author": "john doe"}
        #       perhaps better as env variable
        # TODO: if not favicon: provide one
        # - Template loader
        standard_templates_path = os.path.join(os.getcwd(), 'templates/')
        custom_loader = None
        loader = None
        #  * custom templates
        if templates:
            if os.path.isdir(templates):
                custom_loader = FileSystemLoader(templates)
            else:
                raise Exception("Invalid path to templates: %s" % templates)
        elif not templates and os.path.isdir(standard_templates_path):
            custom_loader = FileSystemLoader(standard_templates_path)
        if not use_package_templates and not custom_loader:
            raise Exception("No templates were found." +
                            "Either set use_package_templates=True or " +
                            "specify templates='/path/to/your/templates/'")
        #  * package Templates
        package_path = os.path.dirname(os.path.abspath(__file__))
        if use_package_templates:
            package_loader = FileSystemLoader(
                os.path.join(package_path, 'base_templates'))
            if custom_loader:
                loader = ChoiceLoader([custom_loader, package_loader])
            else:
                loader = package_loader
        else:
            loader = custom_loader
        #  * sanity check
        if loader is None:
            raise Exception("No templates where found for this project."
                            "\nUse default option 'use_package_templates=True'"
                            "\nOr/and provide a valid path to templates via "
                            "the 'templates' option.")
        self.jinja_env = Environment(
            loader=loader,
            # Note: autoescape stops you from injecting str into template
            #       as in the html_image method for instance
            # autoescape=select_autoescape(['html', 'xml'])
        )
        # - Environment variables
        # env.globals.update(
        # { 'static': staticfiles_storage.url, 'url': reverse, }
        # - Environment methods
        self.jinja_env.globals['url_for'] = self.url_for
        # - Provide Bootstrap Yes/No
        if self.bootstrap_folder is None:
            self.copy_bootstrap = True
            self.bootstrap_folder = os.path.join(package_path, 'bootstrap')
        # Provide Css Style Sheet Yes/No
        if self.css_style_sheet is None:
            self.copy_css = True
            # TODO
            # self.css_style_sheet = os.path.join(package_path, 'style.css')

    def route(self, route, _func=None, **kwargs_deco):
        """


        Route pattern: "/what/ever/route/<type:var1>/.../<type:varN>/..."
            where the different type available are:
            string	accepts any text without a slash (the default)
            int	    accepts integers
            float	like int but for floating point values
            path	like the default but also accepts slashes


        :param route:
        :param _func:
        :param kwargs_deco:
        :return:
        """
        # Note: boiler plate inspired by https://realpython.com/primer-on-python-decorators/#more-real-world-examples
        log.debug("route: %s" % route)
        log.debug("deco kwargs: %s" % kwargs_deco)
        # Separate HTML file name from route
        html_name = "index.html"
        if ".html" in route.split("/")[-1]:
            # TODO: check that there is no logic in the html file name
            html_name = route.split("/")[-1]
            route = route.replace(html_name, '')
        # Generate routes and associated iterator
        reg_expr = r"<\s*?(\b\w+\b)\s*?:\s*?(\b\w+\b)\s*?>"  # <type:var>
        # - base route
        route_pattern = re.sub(reg_expr, "%s", route)
        if route_pattern[0] == '/':  # remove leading '/'...collide with os.path.join
            route_pattern = route_pattern[1:]
        # - variables matches type (if any)
        found = re.findall(reg_expr, route)
        log.debug("Found Var.: %s" % found)
        # - sanity checks:
        if len(found) is not len(kwargs_deco.keys()):
            raise Exception("Number of key variables does not match the number"
                            " of variables specified in the route: %s" % route)
        # - check if names are similar between route and kwargs_deco
        if not [t[1] for t in found] == list(kwargs_deco.keys()):
            raise Exception("There is a mismatch in the naming or the order "
                            "between the kwargs and the variables specify "
                            "in %s" % route)
        # - check if all values in kwargs_deco are of the specified type
        # TODO: moved into a separate _method
        var_lists = []
        for group in found:
            values = kwargs_deco[group[1]]
            if not isinstance(values, list):
                raise Exception("Error type: %s variable must be a list" % group[1])
            if group[0] == "string" and not all(isinstance(n, str) for n in values):
                raise Exception("Error type in %s values. "
                                "'string' type only valid for list of str."
                                "\nE.g. route: %s" % (group[1], route))
            elif group[0] == "int" and not all(isinstance(n, int) for n in values):
                raise Exception("Error type in %s values. "
                                "'int' type only valid for list of int."
                                "\nE.g. route: %s" % (group[1], route))
            elif group[0] == "float" and not all(isinstance(n, float) for n in values):
                raise Exception("Error type in %s values. "
                                "'float' type only valid for list of floats."
                                "\nE.g. route: %s" % (group[1], route))
            # TODO: not sure if I need that check
            elif group[0] == "path" and not all(os.path.exists(n) for n in values):
                raise Exception("Error in %s values. "
                                "Some of those paths do not exist."
                                "\nE.g. route: %s" % (group[1], route))
            elif group[0] not in ["string", "int", "float", "path"]:
                raise Exception("'%s' type in %s is not supported. "
                                "Available types: string, int, float, path. "
                                "\nE.g. route: %s" %
                                (group[0], group[1], route))
            else:
                # - Trimming white spaces beforehand
                if group[0] in ["string", "path"]:
                    values = list(map(str.strip, values))
                var_lists.append(values)
            log.debug("var_lists: %s" % var_lists)
        # - collect route variable(s)
        route_vars = []
        if found:
            route_vars = list(itertools.product(*var_lists))
        log.debug("route_vars: %s" % route_vars)
        # - check if routes already in use, if not store them
        log.debug("Existing routes: %s" % self.routes)
        for vv in route_vars:
            new_route = route_pattern % vv
            log.debug(new_route)
            # TODO: check if route is url and system file friendly
            if new_route not in self.routes:
                self.routes.append(new_route)
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
                if not len(kwargs_deco.keys()) == len(args):
                    raise Exception(
                        "Number of variables in %s does not match the number "
                        "of variables specified in the route" % func.__name__)
                #TODO: - check if names are matching between kwargs_deco and args
                #      Dunno how to do that !? Don't think it is possible
                # if not list(kwargs_deco.keys()) == list(args):
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
                'route_vars': route_vars,
                'view': func}
            log.debug("%s: %s" % (func.__name__, self.web_pages[func.__name__]))
            return wrapped_func

        # Mechanism for handling decorator args & kwargs
        # TODO: not sure whether I need this original block
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
            name: view name or 'static', str
            **kwargs: view arguments as kwargs or 'filename' for static files

        Returns: relative path, str
        """
        # Static
        if name == 'static':
            # search for static file
            if not 'filename' in kwargs.keys():
                raise Exception("'filename' needs to be specify when using "
                                "'static' in url_for")
            path = os.path.join('static', kwargs['filename'])  # for now
            # TODO: Do we want to check if the file actually exist at that level?
        # Views
        elif name in self.web_pages.keys():
            # get url for that particular view
            # TODO: order in kwargs matters here...how do I check that?
            #       perhaps with f"string {name}"
            path = self.web_pages[name]['route_pattern'] % tuple(kwargs.values())
            path = os.path.join(path, self.web_pages[name]['html_name'])
        else:
            log.error("'%s' does not have a url_for" % name)
            return None
        # - make relative path to where it got called
        log.debug("current route: %s " % self.current_route)
        relative_path = os.path.relpath(path, self.current_route)
        log.debug("relative path: %s" % relative_path)
        return relative_path

    def build(self, dest=None, views=[], overwrite=True,
              static_umask=0o644, html_umask=0o644, dir_umask=0o751):
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
        # TODO: add progress bar here
        for name in views:
            route_pattern = self.web_pages[name]['route_pattern']
            route_vars = self.web_pages[name]['route_vars']
            if not route_vars:
                log.debug(os.path.join(self.dest, route_pattern))
                full_paths = [os.path.join(self.dest, route_pattern)]
            else:
                full_paths = []
                for vv in route_vars:
                    full_paths.append(
                        os.path.join(self.dest, route_pattern % vv))
            for full_path in full_paths:
                log.debug("Full path: %s" % full_path)
                if not os.path.exists(full_path):
                    os.makedirs(full_path, self.dir_umask)
        # - Make 'static' folder & move static files where they belong
        self.static_path = os.path.join(self.dest, 'static')
        if not os.path.exists(self.static_path):
            os.makedirs(self.static_path)
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
                elif os.path.isdir(orig):
                    try:
                        shutil.copytree(orig, dest)
                    except FileExistsError as err:
                        if self.overwrite:  # force overwriting
                            shutil.rmtree(dest)
                            shutil.copytree(orig, dest)
                        else:
                            raise err
        # TODO: - Copy CSS style sheet


        # - Apply umasks to static
        self._apply_umask(self.static_path, self.dir_umask, self.static_umask)

        # - Render Templates
        # TODO: add progress bar here
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
                self._write_html_file(html_name, route, rendered_html)
            else:
                for vv in route_vars:
                    #  * inform current page being renderer (for url_for purposes)
                    route = route_pattern % vv
                    self.current_route = route
                    #  * then render
                    rendered_html = view(*vv)
                    #  * finally write to html file
                    self._write_html_file(html_name, route, rendered_html)

    # Hidden Methods
    def _write_html_file(self, html_name, route, rendered_html):
        # Put path together
        html_path = os.path.join(
            self.dest, route, html_name)
        log.debug("html_path: %s" % html_path)
        # Overwrite check
        if os.path.exists(html_path) and not self.overwrite:
            return
        # Write html file
        with open(html_path, "w") as f:
            f.write(rendered_html)
        #  * change permission
        os.chmod(html_path, self.html_umask)

    def _apply_umask(self, path, dir_umask, file_umask):
        for root, dirs, files in os.walk(path):
            for d in dirs:
                os.chmod(os.path.join(root, d), dir_umask)
            for f in files:
                os.chmod(os.path.join(root, f), file_umask)


# Library for "static files"...as in other files than html and bootstrap related
class StaticFile:
    # Storage container for aggregating static file info
    storage = {'name': [], 'type': [], 'source': [], 'destination': []}

    def __init__(self, name, source, dest=None, handle_duplicate=False):
        # Sanity check
        source = os.path.abspath(source)
        if not os.path.isfile(source):
            raise Exception("%s either does not exist or is not a file." % source)
        # Attributes
        self.builder = None
        self.name = name
        self.source = source
        # Note: following line will be overwritten in subclasses
        self.type = ''
        # Fetch existing Builder instance
        self.builder = None
        if Builder.instance:
            self.builder = Builder.instance[0]
        # File Management Strategy
        # - define destination
        if not dest:
            filename = os.path.basename(source)
        elif os.path.splitext(dest)[-1]:  # is the file name  specified in dest?
            filename = dest
        else:
            filename = os.path.join(dest, os.path.basename(source))
        # - some formatting
        if filename[0] == '/':
            filename = filename[1:]
        log.debug("File Name/Destination: %s" % filename)
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
        log.debug("Destination: %s" % self.destination)
        # - aggregating static file info
        self.storage['name'].append(name)
        self.storage['source'].append(source)
        self.storage['destination'].append(self.destination)
        # Note: following line will be overwritten in subclasses
        self.storage['type'].append(self.type)

    @property
    def url(self, current_route=None):
        # Check point: in case this method/class is used outside of
        #              a flastic projects
        if not self.builder and not current_route:
            raise Exception(
                "A flastic.Builder instance must be created beforehand "
                "in order to use the any Static class.\nOtherwise you need "
                "to re-write your template and specify the 'current_route' "
                "option for each 'url' method's call.")
        # - make relative path to where it got called
        dest = os.path.join(self.type, self.destination)
        relative_path = os.path.relpath(dest, self.builder.current_route)
        log.debug("staticfile relative path: %s" % relative_path)
        return relative_path


class Image(StaticFile):
    def __init__(self, dname, source, dest=None):
        super(Image, self).__init__(dname, source, dest=dest)
        # Overwrite StaticFile attributes so that this type of statics end up
        # in their own folder
        self.type = 'images'
        self.storage['type'][-1] = self.type

    @property
    def html_image(self):
        img = '<img src="%s" alt="%s">' % (self.url, self.name)
        log.debug("img: %s" % img)
        return img


class Download(StaticFile):
    def __init__(self, dname, source, dest=None):
        super(Download, self).__init__(dname, source, dest=dest)
        # Overwrite StaticFile attributes so that this type of statics end up
        # in their own folder
        self.type = 'downloads'
        self.storage['type'][-1] = self.type

    @property
    def html_download(self):
        d_link = "<a href='%s' download>%s</a>" % (self.url, self.name)
        log.debug("d_link: %s" % d_link)
        return d_link


def collect_static_files(static_root=None, overwrite=True, copy_locally=False,
                         file_umask=0o644, dir_umask=0o751):
    # Fetch existing Builder instance
    if not Builder.instance and not static_root:
        raise Exception("In order to use this function, one needs to either "
                        "create s flastic.Builder instance beforehand or "
                        "specify a deployment destination via the 'dest' option.")
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


# Flask-lookalikes Library
def render_template(template_name, **context):
    # Fetch existing Builder instance
    if not Builder.instance:
        raise Exception("A flastic.Builder instance must be created beforehand "
                        "in order to use 'render_template'.")
    else:
        jinja_env = Builder.instance[0].jinja_env
    # Get template through jinja template env/loader
    template = jinja_env.get_template(template_name)
    return template.render(**context)
    # print(template.render(**context))


if __name__ == '__main__':
    # TODO: def standard argument parser for flastik projects
    log.setLevel('DEBUG')
    log.addHandler(logging.StreamHandler(sys.stdout))

    website = Builder("https://currents.soest.hawaii.edu/")

    img = Image("random txt",
                "/home/thomas/Desktop/Perso/Empty-wave-at-Colorado_playa_el_gigante.jpg",
                "cruise")

    dwnld = Download("Some text",
                     "/home/thomas/Desktop/Daily_Reports/atl_explorer_logwarning.txt",
                     dest="/test")

    @website.route("/home.html")
    def home():

        context = {'title': "Home",
                   'img': img,
                   'dwnld': dwnld,
                   'body': "Welcome back your home"}
        return render_template('test.html', **context)

    @website.route("/data/<string:ship>/<int:cruise_id>/", ship=["oleander", "bonnevie"], cruise_id=[1,2,6,89,41])
    def data_report(ship, cruise_id):
        context = {'title': ship,
                   'img': img,
                   'dwnld': dwnld,
                   'body': "Here is cruise %s " % cruise_id}

        return render_template('test.html', **context)
    #
    # @website.route("/what/ever/route/<float:a>/<float:b>", a=[1., 2.38, 9.6], b=[9.6, 6.4, 3.2])
    # def multiply(a, b):
    #     print("A * B =", a*b)
    #
    #
    # @website.route("/what/ever/route/<string:txt>/<int:id>/<string:cruise>/",
    #                txt=["hello ", "world"],
    #                id=[1, 2, 6, 3],
    #                cruise=["t5", "rygefh", "gerh66", "srgjfpgj"],)
    # def test_print_2(txt, id, cruise):
    #     print(id, ":", txt, ":", cruise)


    website.build() #dest="./test_build")  #, views=['home', 'test_print_2'])
    collect_static_files(copy_locally=True)
