"""
Facade for Google App Engine's datastore services (ndb).
Re-exports the ndb module and all its contents.
"""
# Import the actual ndb module to preserve its structure (including ndb.model submodule)
from google.appengine.ext import ndb

# Also re-export all ndb contents for convenience
from google.appengine.ext.ndb import *


def _urlsafe_str(self):
	"""Like urlsafe(), but returns str (py3 urlsafe() returns bytes).

	Added as a NEW method rather than replacing urlsafe(): bundled ndb's
	in-context memcache concatenates bytes with key.urlsafe() internally,
	so changing urlsafe()'s return type breaks every put().
	"""
	return self.urlsafe().decode()


ndb.Key.urlsafe_str = _urlsafe_str
ndb.Cursor.urlsafe_str = _urlsafe_str
