#!/usr/bin/env python
"""
Flastik - A Flask-like Tiny-framework for static websites.
(c) Copyright 2019-2026. See LICENSE for details.

Renders docs/manual.md into flastik/README.pdf, the manual shipped inside
the package and linked from the generated documentation website.

The Markdown subset understood here is deliberately small -- headings
(# / ##), bullet lists (- ), fenced code blocks (```) and paragraphs --
because that is all manual.md uses. Run it with:

    pip install reportlab
    python docs/build_manual.py
"""
import os
import re
import sys

from reportlab import rl_config
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
)
from reportlab.platypus.tableofcontents import TableOfContents

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SOURCE = os.path.join(HERE, "manual.md")
TARGET = os.path.join(REPO, "flastik", "README.pdf")

COPYRIGHT = "Flastik - Copyright 2019-2026"


def get_version():
    """Reads __version__ out of flastik/__init__.py without importing it."""
    init_py = os.path.join(REPO, "flastik", "__init__.py")
    with open(init_py) as f:
        match = re.search(r"^__version__\s*=\s*['\"]([^'\"]+)['\"]", f.read(), re.MULTILINE)
    if not match:
        raise RuntimeError("Could not find __version__ in %s" % init_py)
    return match.group(1)


def make_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="CoverTitle", parent=styles["Title"], fontSize=24, leading=30,
        spaceAfter=36))
    styles.add(ParagraphStyle(
        name="CoverSubTitle", parent=styles["Normal"], fontSize=14, leading=20,
        alignment=TA_CENTER))
    styles.add(ParagraphStyle(
        name="H1", parent=styles["Heading1"], fontSize=16, leading=20,
        spaceBefore=18, spaceAfter=10))
    styles.add(ParagraphStyle(
        name="H2", parent=styles["Heading2"], fontSize=13, leading=17,
        spaceBefore=14, spaceAfter=8))
    styles.add(ParagraphStyle(
        name="TOCTitle", parent=styles["Heading1"], fontSize=16, leading=20,
        spaceBefore=18, spaceAfter=10))
    styles.add(ParagraphStyle(
        name="Body", parent=styles["BodyText"], fontSize=10.5, leading=14,
        spaceAfter=8))
    styles.add(ParagraphStyle(
        name="ListItem", parent=styles["BodyText"], fontSize=10.5, leading=14,
        leftIndent=18, bulletIndent=6, spaceAfter=4))
    styles.add(ParagraphStyle(
        name="CodeBlock", parent=styles["Code"], fontSize=8.5, leading=10.5,
        leftIndent=12, spaceBefore=6, spaceAfter=10))
    return styles


def escape(text):
    """Escapes the handful of characters ReportLab treats as markup."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # `code` -> monospace
    return re.sub(r"`([^`]+)`", r'<font face="Courier">\1</font>', text)


def parse(markdown, styles):
    """Turns the Markdown subset into a list of platypus flowables."""
    story = []
    lines = markdown.splitlines()
    index = 0
    paragraph = []
    bullet = []

    def flush():
        """Emits any pending paragraph/bullet text."""
        if paragraph:
            story.append(Paragraph(escape(" ".join(paragraph)), styles["Body"]))
            del paragraph[:]
        if bullet:
            story.append(Paragraph(
                escape(" ".join(bullet)), styles["ListItem"], bulletText="•"))
            del bullet[:]

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush()
            index += 1
            block = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                block.append(lines[index])
                index += 1
            story.append(Preformatted("\n".join(block), styles["CodeBlock"]))
        elif stripped.startswith("## "):
            flush()
            story.append(Paragraph(escape(stripped[3:]), styles["H2"]))
        elif stripped.startswith("# "):
            flush()
            story.append(Paragraph(escape(stripped[2:]), styles["H1"]))
        elif stripped.startswith("- "):
            flush()
            bullet.append(stripped[2:])
        elif not stripped:
            flush()
        elif bullet:
            # Continuation line of the current bullet.
            bullet.append(stripped)
        else:
            paragraph.append(stripped)
        index += 1

    flush()
    return story


class ManualTemplate(BaseDocTemplate):
    """Adds heading -> table-of-contents notifications and page furniture."""

    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):
            return
        style = flowable.style.name
        if style == "H1":
            self.notify("TOCEntry", (0, flowable.getPlainText(), self.page))
        elif style == "H2":
            self.notify("TOCEntry", (1, flowable.getPlainText(), self.page))


def decorate(canvas, doc):
    """Draws the page number and copyright footer."""
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(letter[0] / 2.0, 0.5 * inch, str(canvas.getPageNumber()))
    canvas.drawRightString(letter[0] - inch, 0.5 * inch, COPYRIGHT)
    canvas.restoreState()


def build():
    # Suppresses the embedded timestamp and random document id, so that
    # rebuilding unchanged sources produces a byte-identical PDF instead of
    # a spurious binary diff in git.
    rl_config.invariant = 1

    with open(SOURCE) as f:
        markdown = f.read()

    version = get_version()
    styles = make_styles()

    doc = ManualTemplate(
        TARGET, pagesize=letter,
        leftMargin=inch, rightMargin=inch,
        topMargin=inch, bottomMargin=inch,
        title="Flastik %s - Specifications, Syntax & Patterns" % version,
        author="Dr. Thomas Roc")

    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[frame]),
        PageTemplate(id="body", frames=[frame], onPage=decorate),
    ])

    story = [
        Spacer(1, 2 * inch),
        Paragraph("Flastik %s" % version, styles["CoverTitle"]),
        Paragraph("Specifications, Syntax &amp; Patterns", styles["CoverSubTitle"]),
        Spacer(1, 0.4 * inch),
        Paragraph("A tiny-framework for static website design", styles["CoverSubTitle"]),
        Spacer(1, 2 * inch),
        Paragraph(COPYRIGHT, styles["CoverSubTitle"]),
        NextPageTemplate("body"),
        PageBreak(),
        # Deliberately not styled "H1": afterFlowable would list it in itself.
        Paragraph("Table of Contents", styles["TOCTitle"]),
    ]

    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(name="TOC1", fontSize=11, leading=16),
        ParagraphStyle(name="TOC2", fontSize=10, leading=14, leftIndent=20),
    ]
    story.append(toc)
    story.append(PageBreak())
    story.extend(parse(markdown, styles))

    # multiBuild resolves the table of contents' page numbers.
    doc.multiBuild(story)
    print("Wrote %s (version %s)" % (TARGET, version))


if __name__ == "__main__":
    sys.exit(build())
