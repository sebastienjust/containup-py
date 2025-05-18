import os
import sys

sys.path.insert(0, os.path.abspath("../../containup"))

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "containup"
copyright = "2025, Sébastien JUST"
author = "Sébastien JUST"
release = "v0.1.7"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",  # support Google/Numpy-style docstrings
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",  # Manage TODO in documentation
    "sphinx.ext.githubpages",  # Creates a .nojekyll file in docs/build/html so that GitHub Pages don't think it's Jekyll and make _static/ directories work.
    "myst_parser",  # Markdown
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

autodoc_class_signature = "separated"
myst_enable_extensions = ["colon_fence"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
html_theme_options = {
    "source_repository": "https://github.com/sebastienjust/containup-py",
    "source_branch": "main",
    "source_directory": "docs/",
}

# -- Napoleon settings -------------------------------------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = True
