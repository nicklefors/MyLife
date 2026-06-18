"""
Facade for Google App Engine's runtime module.
Re-exports runtime utilities and exceptions.
"""
from google.appengine import runtime
from google.appengine.runtime import *
from google.appengine.api import runtime as api_runtime