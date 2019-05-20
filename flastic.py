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

# Standard logging
log = logging.getLogger(__name__)


class Builder:
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
        self.css_style_sheet = css_style_sheet
        self.dest = None
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
            autoescape=select_autoescape(['html', 'xml'])
        )
        # - Environment variables
        # env.globals.update(
        # { 'static': staticfiles_storage.url, 'url': reverse, }
        # - Environment methods
        self.jinja_env.globals['url_for'] = self.url_for
        # TODO: bootstrap (package, custom, ...
        if self.bootstrap_folder is None:
            self.bootstrap_folder = os.path.join(package_path, 'bootstrap')
        # TODO: handle CSS style sheet...usually stored in static/style.css.

    def route(self, route, _func=None, **kwargs_deco):
        """


        Route pattern: "/what/ever/route/<type:var1>/.../<type:varn>/..."
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
        # TODO: restart here
        # Static
        if name == 'static':
            # search for static file
            # TODO: check if kwargs are valid
            # TODO
            path = os.path.join('static', kwargs['filename'])  # for now
        # Views
        elif name in self.web_pages.keys():
            # TODO: order in kwargs matters here...how do I check that?
            #       perhaps with f"string {name}"
            path = self.web_pages[name]['route_pattern'] % tuple(kwargs.values())
            path = os.path.join(path, self.web_pages[name]['html_name'])
        else:
            # get url for that particular view
            log.error("'%s' does not have a url_for" % name)
            return None
        # - make relative path to where it got called
        log.debug("current route: %s " % self.current_route)
        relative_path = os.path.relpath(path, self.current_route)
        log.debug("relative path: %s" % relative_path)
        return relative_path

    def build(self, dest=None, views=[],
              overwrite_html=True, copy_bootstrap=True,
              static_umask=0o644, html_umask=0o644, dir_umask=0o751):
        # New attributes...not compliant with PEP but whatever
        self.overwrite_html = overwrite_html
        self.copy_bootstrap = copy_bootstrap
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
        # TODO: - Make 'static' folder & move static files where they belong
        static_path = os.path.join(self.dest, 'static')
        # TODO: - Make 'static' folder & move static files where they belong
        if not os.path.exists(static_path):
            os.makedirs(static_path)
        # TODO: copy bootstrap & custom CSS style sheet
        if self.copy_bootstrap:
            for ff in os.listdir(self.bootstrap_folder):
                orig = os.path.join(self.bootstrap_folder, ff)
                dest = os.path.join(static_path, ff)
                if os.path.isfile(orig):
                    shutil.copy(orig, dest)
                elif os.path.isdir(orig):
                    shutil.copytree(orig, dest)

        # - Apply umasks to static
        self._apply_umask(static_path, self.dir_umask, self.static_umask)

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



    def _write_html_file(self, html_name, route, rendered_html):
        # Put path together
        html_path = os.path.join(
            self.dest, route, html_name)
        log.debug("html_path: %s" % html_path)
        # Overwrite check
        if os.path.exists(html_path) and not self.overwrite_html:
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



# TODO: class Static...dev in a different file
# TODO: class Downloadable...dev in a different file
# TODO: def render_template(...)...bombs if no Builder is set (look in namespace)
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

    @website.route("/home.html")
    def home():
        context = {'title': "Home",
                   'body': "Welcome back your home"}
        return render_template('test.html', **context)

    @website.route("/data/<string:ship>/<int:cruise_id>/", ship=["oleander", "bonnevie"], cruise_id=[1,2,6,89,41])
    def data_report(ship, cruise_id):
        context = {'title': ship,
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


