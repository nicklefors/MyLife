"""Template facade.

Historically a thin wrapper around ``google.appengine.ext.webapp.template``
(Django 1.x).  That module does not exist on the python3 runtime, so this is now
backed directly by the Django 4.2 template engine while preserving the
symbols the codebase depends on:

    render(path, context)        -> rendered string (path may be absolute or
                                    relative to the app root / templates dir)
    Template(source, debug)      -> compiled template from a string (datastore
                                    PageTemplate content); render with Context
    Context(dict)                -> render context for Template
    create_template_register()   -> a django.template.Library (for @register.filter)
    register_template_library()  -> no-op; custom libraries are registered as
                                    ``builtins`` in django_settings.TEMPLATES
"""
import os

from django import template as _django_template
from django.template import engines
from django.template.loader import get_template


def Template(template_string, debug=False, name=None):
    """Compile a template from a string (datastore-stored PageTemplate content).

    Matches the legacy ``webapp.template.Template(source, debug)`` call shape;
    ``debug``/``name`` are accepted and ignored (the legacy second positional
    arg must NOT be forwarded as ``origin`` — ``origin=False`` breaks Django's
    error paths).  ``django.template.Template`` with no explicit engine uses
    ``Engine.get_default()`` — the sole DjangoTemplates backend from
    ``django_settings.TEMPLATES`` — so the custom filter ``builtins`` and
    ``string_if_invalid`` apply, and ``.render()`` accepts a ``Context``.
    """
    return _django_template.Template(template_string)


Context = _django_template.Context


def create_template_register():
    """Return a fresh tag/filter registry.

    The legacy ``webapp.template.create_template_register`` returned a Django
    template ``Library``; ``django.template.Library`` is the modern equivalent
    and supports the same ``@register.filter`` / ``@register.tag`` decorators.
    """
    return _django_template.Library()


def register_template_library(library_name):
    """Compatibility no-op.

    Under the old runtime this registered a filter/tag library globally.  The
    same effect is now achieved declaratively via ``OPTIONS['builtins']`` in
    ``django_settings.TEMPLATES``.  Kept so existing call sites need no change.
    """
    return None


def _to_template_name(path):
    """Map a render() ``path`` to a name the Django loader can resolve.

    Most call sites pass an absolute path built with
    ``os.path.join(os.path.dirname(__file__), 'templates/foo.html')``; a few
    pass the relative ``'templates/foo.html'`` directly.  Absolute paths are
    made relative to the longest matching configured template DIR so the
    loader (and thus ``{% extends %}`` / ``{% include %}``) resolves them.
    """
    if not os.path.isabs(path):
        return path
    abspath = os.path.abspath(path)
    dirs = [os.path.abspath(d) for d in engines['django'].engine.dirs]
    for d in sorted(dirs, key=len, reverse=True):
        if abspath == d:
            continue
        if abspath.startswith(d + os.sep):
            return os.path.relpath(abspath, d)
    return os.path.relpath(abspath)


def render(path, context=None):
    """Render the template at ``path`` with ``context`` and return a string,
    matching the old ``webapp.template.render(path, dict)`` signature."""
    return get_template(_to_template_name(path)).render(context or {})
