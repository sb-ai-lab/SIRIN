"""Standalone guard programs written verbatim into experiment workspaces.

Each module here is read as text by ``evolution.eval.workspace_guard`` and
written into a generated workspace to run in a *separate* interpreter (a
PATH command wrapper or a ``sitecustomize`` hook). They are deliberately not
imported by the package itself.
"""
