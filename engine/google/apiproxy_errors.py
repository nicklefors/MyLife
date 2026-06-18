"""API proxy errors facade.

appengine-python-standard exposes apiproxy_errors under google.appengine.runtime;
some SDK builds also mirror it under google.appengine.api. Try both so this works
regardless of the installed layout.
"""
try:
    from google.appengine.api.apiproxy_errors import *
except ImportError:
    from google.appengine.runtime.apiproxy_errors import *
