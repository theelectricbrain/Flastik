#!/usr/bin/env python
import os
import re
import sys
import logging


from functools import wraps
import itertools




from jinja2 import (Environment, ChoiceLoader, PackageLoader, FileSystemLoader,
                    select_autoescape)

# Standard logging
log = logging.getLogger(__name__)


class Builder:
    # Container for web page = view + var(s) + route pattern + html name
    web_pages = {}
    routes = []

    def __init__(self, website_name,
                 templates=None,
                 bootstrap_folder=None,
                 css_style_sheet=None,
                 use_package_templates=True):
        # Environment
        # - Various attributes
        self.dest = None
        # - template loader
        standard_templates_path = os.path.join(os.getcwd(), 'templates/')
        custom_loader = None
        #  * Custom templates
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
        #  * Package Templates
        # if use_package_templates:
        #     package_loader = FileSystemLoader(os.getcwd(), 'templates')
        #     loader = ChoiceLoader([custom_loader, package_loader])
        # else:
        #     loader = custom_loader
        # self.jinja_env = Environment(
        #     loader=loader,
        #     autoescape=select_autoescape(['html', 'xml'])
        # )
        # TODO: bootstrap (package, custom, ...
        # TODO: def build

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
        # Generate routes and associated iterator
        reg_expr = r"<\s*?(\b\w+\b)\s*?:\s*?(\b\w+\b)\s*?>"  # <type:var>
        # - base route
        route_pattern = re.sub(reg_expr, "%s", route)
        # - html name
        html_name = "index.html"
        if ".html" in route.split("/")[-1]:
            html_name = route.split("/")[-1]
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
        # TODO: separated into _method
        var_lists = []
        for group in found:
            values = kwargs_deco[group[1]]
            if not isinstance(values, list):
                raise Exception("Error type: %s variable must be a list" % group[1])
            if group[0] == "string" and not all(isinstance(n, (str, bytes)) for n in values):
                raise Exception("Error type in %s values. "
                                "'string' type only valid for list of str or bytes."
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
                # - Trimming whie spaces beforehand
                if group[0] in ["string", "path"]:
                    values = list(map(str.strip, values))
                var_lists.append(values)
            log.debug("var_lists: %s" % var_lists)
        # - route variable(s)
        route_vars = []
        if found:
            route_vars = list(itertools.product(*var_lists))
        log.debug("route_vars: %s" % route_vars)
        # - check if routes already in use, if not store it
        log.debug("Existing routes: %s" % self.routes)
        for vv in route_vars:
            new_route = route_pattern % vv
            log.debug(new_route)
            if new_route not in self.routes:
                self.routes.append(new_route)
            else:
                raise Exception("Change route pattern and/or variables: "
                                "%s already used by another view" % new_route)

        # TODO: check and generate routes
        def wrapper(func):
            @wraps(func)
            def wrapped_func(*args, **kwargs):
                if args:
                    log.debug("*args: %s" % list(args))
                if kwargs:
                    log.debug("**kwargs: %s" % list(kwargs))
                # Sanity checks:
                # - check if cortresponding amount of variables
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
            return wrapped_func

        # Mechanism for handling decorator args & kwargs
        # TODO: not sure whether I need this original block
        # if _func is None:
        #     wrapper
        # else:
        #     return wrapper(_func)
        return wrapper

    def build(self, dest=None, views=[],
              overwrite_html=False, overwrite_bootstrap=True):
        # Sanity checks
        if not dest:
            self.dest = os.getcwd()
        else:
            if os.path.isdir(dest):
                self.dest = dest
            else:
                raise Exception("the provided destination does not exist: %s"
                                % dest)
        log.debug("Website destination: %s" % dest)
        if not type(views) == list:
            views = [views]
        if not views:
            views = self.web_pages.keys()
        # Building static website
        # TODO: add progress bar here
        for name in views:
            log.info("%s: %s" % (name, self.web_pages[name]))
            route_pattern = self.web_pages[name]['route_pattern']
            route_vars = self.web_pages[name]['route_vars']
            html_name = self.web_pages[name]['html_name']
            view = self.web_pages[name]['view']

            # - run function over for loop of routes
            if not route_vars:
                view()
            else:
                # TODO: add progress bar here
                for vv in route_vars:
                    # TODO: rendered_html = view(vv)
                    view(*vv)
                    # TODO: make dirs and html
            # TODO: copy bootstrap & CSS style sheet


if __name__ == '__main__':
    website = Builder('test')
    log.setLevel('INFO')
    log.addHandler(logging.StreamHandler(sys.stdout))

    @website.route("/home")
    def home_print():
        print("home")

    @website.route("/what/ever/route/<string:txt>/<int:id>", txt=["hello ", "world"], id=[1,2,6,3])
    def test_print(txt, id):
        print(id, ":", txt)


    @website.route("/what/ever/route/<string:txt>/<int:id>/<string:cruise>/",
                   txt=["hello ", "world"], id=[1,2,6,3], cruise=["t5", "rygefh", "gerh66", "srgjfpgj"],)
    def test_print_2(txt, id, cruise):
        print(id, ":", txt, ":", cruise)


    website.build()  # views=['home_print', 'test_print_2'])


