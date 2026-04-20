"""Sphinx configuration for the gotime documentation site."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath("../src"))

project = "gotime"
author = "GoTime Contributors"
copyright = "2015-2026, GoTime Contributors"

from gotime import __version__  # noqa: E402

release = __version__
version = ".".join(__version__.split(".")[:2])

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "sphinxcontrib.mermaid",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "linkify",
    "smartquotes",
    "tasklist",
]

# Treat ```mermaid fences as the `mermaid` directive rather than as a code
# block with an unknown pygments lexer.
myst_fence_as_directive = ["mermaid"]

html_theme = "furo"
html_title = f"gotime {release}"
html_static_path: list[str] = []
