"""Remote API facade — deferred on the python3 runtime.

``google.appengine.ext.remote_api.handler`` and
``google.appengine.ext.webapp.util.run_wsgi_app`` are not available under
python3 bundled services.  Remote API admin tooling is deferred; this module is
retained only so imports stay clean.  See ``remote_api.py`` (app root).
"""

handler = None
run_wsgi_app = None
