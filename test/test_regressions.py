#!/usr/bin/env python
"""
Flastik - A Flask-like Tiny-framework for static websites.
(c) Copyright 2019-2026. See LICENSE for details.

Focused regression tests for behaviour the end-to-end build in
test_flastik.py does not exercise. Each test here stands on its own: the
'clean_state' fixture below resets the process-wide class state that
Builder and StaticFile keep, so these can be run individually and in any
order.
"""
import logging
import os
import sys

import pytest

import flastik
from flastik import Builder, Download, Image, cli, collect_static_files, render_template
from flastik.flastik import StaticFile

# Note: resolved off the installed package, so these tests do not care which
#       directory pytest was started from.
PACKAGE_PATH = os.path.dirname(os.path.abspath(flastik.__file__))
ICON = os.path.join(PACKAGE_PATH, "base_templates", "default_icon.png")


def reset_state():
    """
    Views and routes live on the Builder instance, but the registry of
    Builders and the static file storage are still process wide. Put both
    back to their as-imported state.
    """
    Builder.instance.clear()
    Builder._rendering = None
    for values in StaticFile.storage.values():
        values.clear()
    # Builder.__init__ attaches a fresh file handler every time
    log = logging.getLogger("flastik.flastik")
    for handler in list(log.handlers):
        log.removeHandler(handler)
        handler.close()


@pytest.fixture(autouse=True)
def clean_state():
    reset_state()
    yield
    reset_state()


# Builder
def test_meta_default_is_not_shared_between_instances():
    """The 'description'/'author' shorthands must not leak into the next
    Builder via a mutable default argument."""
    first = Builder(description="first site", author="somebody")
    second = Builder()

    assert first.meta["description"] == "first site"
    assert second.meta == {}


def test_meta_argument_is_not_mutated_by_caller():
    """A caller's dict must survive being passed as 'meta'."""
    caller_meta = {"generator": "flastik"}
    Builder(meta=caller_meta, description="a description")
    assert caller_meta == {"generator": "flastik"}


def test_two_builders_can_coexist():
    """Regression: Builder used to refuse a second instance, because its
    views and routes were shared class-wide."""
    first = Builder()
    second = Builder()
    assert first is not second


def test_views_do_not_leak_between_builders():
    first = Builder()
    second = Builder()

    @first.route("/only_on_first.html")
    def only_on_first():
        return "first"

    @second.route("/only_on_second.html")
    def only_on_second():
        return "second"

    assert list(first.web_pages) == ["only_on_first"]
    assert list(second.web_pages) == ["only_on_second"]


def test_routes_do_not_leak_between_builders():
    # Note: only routes carrying variables are recorded in 'routes'; a
    #       static route expands to nothing to iterate over.
    first = Builder()
    second = Builder()

    @first.route("/<string:ship>/index.html", ship=["ariel"])
    def first_pages(ship):
        return ship

    @second.route("/<string:ship>/index.html", ship=["bounty"])
    def second_pages(ship):
        return ship

    assert first.routes == [os.path.join("ariel", "index.html")]
    assert second.routes == [os.path.join("bounty", "index.html")]


def test_same_route_may_be_used_by_two_builders():
    """Two web sites are free to have a page at the same url: the routes of
    one used to collide with the routes of the other."""
    first = Builder()
    second = Builder()

    @first.route("/<string:ship>/index.html", ship=["ariel"])
    def home_of_first(ship):
        return "first"

    # Would previously raise "already used by another view"
    @second.route("/<string:ship>/index.html", ship=["ariel"])
    def home_of_second(ship):
        return "second"

    assert first.routes == second.routes == [os.path.join("ariel", "index.html")]


def test_route_collision_within_one_builder_still_raises():
    website = Builder()

    @website.route("/<string:ship>/index.html", ship=["ariel"])
    def a_view(ship):
        return ""

    with pytest.raises(Exception, match="already used by another view"):

        @website.route("/<string:ship>/index.html", ship=["ariel"])
        def another_view(ship):
            return ""


def test_url_for_is_resolved_against_its_own_builder():
    first = Builder()
    second = Builder()

    @first.route("/deep/page.html")
    def a_page():
        return ""

    assert first.url_for("a_page") == os.path.join("deep", "page.html")
    # 'second' knows nothing of that view
    assert second.url_for("a_page") is None


def test_current_returns_the_most_recent_builder():
    first = Builder()
    assert Builder.current() is first
    second = Builder()
    assert Builder.current() is second


def test_current_raises_when_no_builder_exists():
    with pytest.raises(Exception, match="must be created beforehand"):
        Builder.current()


def test_each_builder_renders_with_its_own_templates(tmp_path):
    """A view must render through the Builder being built, even though a
    more recent Builder is the current one."""
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "page.html").write_text("from the first builder")

    first = Builder(template_dirs=str(templates))

    @first.route("/index.html")
    def home():
        return render_template("page.html")

    # A second Builder, which cannot see that template, becomes current
    Builder()
    assert Builder.current() is not first

    first.build(dest=str(tmp_path / "site"))
    assert (tmp_path / "site" / "index.html").read_text() == "from the first builder"
    # ...and the current Builder is restored once the build is over
    assert Builder._rendering is None


def test_builds_only_write_their_own_pages(tmp_path):
    first = Builder()
    second = Builder()

    @first.route("/from_first.html")
    def from_first():
        return "first"

    @second.route("/from_second.html")
    def from_second():
        return "second"

    first.build(dest=str(tmp_path / "first_site"))
    assert (tmp_path / "first_site" / "from_first.html").is_file()
    assert not (tmp_path / "first_site" / "from_second.html").exists()


def test_route_rejects_mismatched_variable_count():
    website = Builder()
    with pytest.raises(Exception, match="Number of key variables"):
        website.route("/<string:ship>/<int:cruise_id>/", ship=["a"])


# Static files
def test_image_and_download_may_share_a_name():
    """Separate deployment folders mean the destinations do not clash."""
    Builder()
    image = Image("logo", ICON, dest="logo.png")
    download = Download("logo", ICON, dest="logo.png")
    plain = StaticFile("logo", ICON, dest="logo.png")

    assert (image.type, image.destination) == ("images", "logo.png")
    assert (download.type, download.destination) == ("downloads", "logo.png")
    assert (plain.type, plain.destination) == ("files", "logo.png")


def test_same_type_duplicate_still_raises():
    Builder()
    Image("logo", ICON, dest="logo.png")
    with pytest.raises(Exception, match="images/logo.png is already in use"):
        Image("logo again", ICON, dest="logo.png")


def test_handle_duplicate_puts_the_second_file_in_its_own_folder():
    """Regression: this used to raise TypeError by joining a UUID object."""
    Builder()
    first = Image("logo", ICON, dest="logo.png")
    second = Image("logo again", ICON, dest="logo.png", handle_duplicate=True)

    assert first.destination == "logo.png"
    assert second.destination != first.destination
    assert os.path.basename(second.destination) == "logo.png"
    # ...namely a uuid4 sub-folder
    assert len(os.path.dirname(second.destination)) == 36


def test_statics_do_not_leak_between_sites(tmp_path):
    """Regression: collect_static_files() used to deploy every static file
    ever created, so each site shipped the previous sites' assets."""
    Builder()
    Image("first", ICON, dest="first.png")
    collect_static_files(
        static_root=str(tmp_path / "first_site"), copy_locally=True)

    Builder()
    Image("second", ICON, dest="second.png")
    collect_static_files(
        static_root=str(tmp_path / "second_site"), copy_locally=True)

    assert os.listdir(tmp_path / "first_site" / "images") == ["first.png"]
    assert os.listdir(tmp_path / "second_site" / "images") == ["second.png"]


def test_each_site_may_reuse_a_file_name():
    """Regression: two web sites could not each have an images/logo.png."""
    Builder()
    first = Image("logo", ICON, dest="logo.png")
    Builder()
    second = Image("logo", ICON, dest="logo.png")

    assert first.destination == second.destination == "logo.png"
    assert first.builder is not second.builder


def test_collect_static_files_accepts_an_explicit_builder(tmp_path):
    """A site may be collected once it is no longer the current one."""
    first = Builder()
    Image("first", ICON, dest="first.png")
    Builder()  # becomes the current Builder
    Image("second", ICON, dest="second.png")

    collect_static_files(
        static_root=str(tmp_path / "site"), copy_locally=True, builder=first)

    assert os.listdir(tmp_path / "site" / "images") == ["first.png"]


def test_statics_created_before_any_builder_are_still_collected(tmp_path):
    """StaticFile does not require a Builder; those files have no site of
    their own and go wherever they are collected."""
    StaticFile("early", ICON, dest="early.png")
    assert StaticFile.storage["builder"] == [None]

    collect_static_files(static_root=str(tmp_path / "site"), copy_locally=True)
    assert (tmp_path / "site" / "files" / "early.png").is_file()


def test_collect_static_files_reports_when_there_is_nothing(tmp_path, capsys):
    """Regression: the guard tested the storage dict, which is never empty,
    so this branch was unreachable."""
    collect_static_files(static_root=str(tmp_path))
    assert "no static files to collect" in capsys.readouterr().out


def test_download_size_is_humanized(tmp_path):
    target = tmp_path / "payload.bin"
    target.write_bytes(b"\0" * 2048)
    assert Download("payload", str(target)).size == "2.0 KB"


def test_download_size_stops_at_the_largest_suffix(tmp_path, monkeypatch):
    """Regression: the loop used to run off the end of the suffix list."""
    target = tmp_path / "huge.bin"
    target.write_bytes(b"\0")
    download = Download("huge", str(target))
    monkeypatch.setattr(os.path, "getsize", lambda _: 1024 ** 6)
    assert download.size.endswith(" TB")


# Command line interface
def test_main_uses_its_argument_rather_than_sys_argv(tmp_path, monkeypatch):
    """Regression: main() accepted 'args' but then re-read sys.argv."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["flastik"])  # deliberately empty
    cli.main(["--create_project", "demo"])
    assert (tmp_path / "demo" / "demo.py").is_file()


def test_escape_doc_handles_undocumented_objects():
    """Regression: build_doc crashed on any member without a docstring."""

    class Sample:
        def documented(self):
            """Takes a <list> of things."""

        def undocumented(self):
            pass

    assert cli.escape_doc(Sample.documented) == "Takes a &lt;list&gt; of things."
    assert cli.escape_doc(Sample.undocumented) == ""
