"""
Google App Engine facade module.
This module provides a clean abstraction over Google App Engine services.

Uses lazy loading via __getattr__ to avoid circular import issues while
allowing all wrapper modules to use explicit absolute imports.
"""

import sys

# Define all available modules
__all__ = [
    'ndb', 'db', 'identity', 'search', 'memcache', 'taskqueue',
    'cache', 'tasks', 'storage',
    'images', 'blobstore', 'webapp', 'mail_handlers', 'appstats',
    'runtime', 'vendor', 'datastore_errors'
]

# Cache for loaded modules to avoid reimporting
_module_cache = {}


def __getattr__(name):
    """
    Lazy-load submodules on demand.

    This prevents circular import issues by only importing modules when
    they are explicitly requested, rather than eagerly importing all
    modules when the package is first imported.
    """
    if name in __all__:
        # Check if already cached
        if name in _module_cache:
            return _module_cache[name]

        # Import the module dynamically
        module_path = 'engine.google.{}'.format(name)
        try:
            __import__(module_path)
            module = sys.modules[module_path]
            _module_cache[name] = module
            return module
        except ImportError as e:
            raise AttributeError(
                "module 'engine.google' has no attribute '{}'".format(name)
            )

    raise AttributeError("module 'engine.google' has no attribute '{}'".format(name))
