"""
Flastik - A Flask-like Tiny-framework for static websites.
(c) Copyright 2019-2026. See LICENSE for details.
"""

# Meta
__version__ = '1.0.3'
__description__ = 'A Flask-like Tiny-framework for static websites'
__author__ = 'Dr. Thomas Roc'
__author_email__ = 'info@electricbrain.fr'
__license__ = 'GNU GPLv3'

from .flastik import (
    Builder,
    Download,
    FlastikError,
    Image,
    StaticFile,
    add_build_arguments,
    add_Builder_arguments,
    add_collect_static_files_arguments,
    apply_umasks,
    check_path_for_illegal_characters,
    check_url_for_unsafe_characters,
    collect_static_files,
    render_template,
    rst2html,
)

__all__ = [
    "Builder",
    "Download",
    "FlastikError",
    "Image",
    "StaticFile",
    "add_Builder_arguments",
    "add_build_arguments",
    "add_collect_static_files_arguments",
    "apply_umasks",
    "check_path_for_illegal_characters",
    "check_url_for_unsafe_characters",
    "collect_static_files",
    "render_template",
    "rst2html",
]

