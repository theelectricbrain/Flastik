#!/usr/bin/env python
"""
Flastik - A Flask-like Tiny-framework for static websites.
(c) Copyright 2019-2025. See LICENSE for details.
"""

# Meta
__version__ = '1.0'
__description__ = 'A Flask-like Tiny-framework for static websites'
__author__ = 'Dr. Thomas Roc'
__author_email__ = 'info@electricbrain.fr'
__license__ = 'GNU GPLv3'

from .flastik import (
    Builder, 
    check_url_for_unsafe_characters,
    check_path_for_illegal_characters,
    apply_umasks,
    add_Builder_arguments,
    add_build_arguments,
    rst2html,
    render_template,
    StaticFile,
    Image,
    Download,
    collect_static_files,
    add_collect_static_files_arguments,
)

__all__ = [
    "Builder",
    "check_url_for_unsafe_characters",
    "check_path_for_illegal_characters",
    "apply_umasks",
    "add_Builder_arguments",
    "add_build_arguments",
    "rst2html",
    "render_template",
    "StaticFile",
    "Image",
    "Download",
    "collect_static_files",
    "add_collect_static_files_arguments",
]

