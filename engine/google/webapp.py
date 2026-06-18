"""Legacy ``webapp`` facade.

``google.appengine.ext.webapp`` is gone on the python3 runtime.  The framework
is webapp2 throughout, so this facade simply re-exports the webapp2 equivalents
for the handful of legacy references that remain.  The template helpers live in
``engine.google.template`` and blobstore handlers in
``engine.google.blobstore_handlers``.
"""
import webapp2
from webapp2 import (
    WSGIApplication,
    RequestHandler,
    Request,
    Response,
    redirect,
)
