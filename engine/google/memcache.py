"""
Facade for Google App Engine's Memcache.

All CMS app code imports memcache from here. Keys are transparently
versioned with KEY_PREFIX so the py3 app never reads cache entries written
by the py2 app: py2 stored plain `str` values with flag TYPE_STR, which the
py3 runtime returns as raw bytes (json.dumps -> TypeError, '%s' -> b'...'
garbage, str+bytes -> TypeError). Prefixing the keys orphans every py2-era
entry at once instead of type-guarding each read site; old entries age out
via normal eviction. See pickle_compat.py for the pickled-value half of the
same problem.

Deliberately NOT prefixed (they bypass this facade and import the real
google.appengine.api.memcache): webapp2_extras sessions (raw sid keys,
covered by pickle_compat), and bundled ndb's internal cache ('NDB9:' keys).

Module-level functions are used (not a private Client) so the latin-1
unpickler installed by pickle_compat.setup_client() stays in effect.
"""

from google.appengine.api.memcache import *
from google.appengine.api import memcache as _memcache

# Bump to invalidate the entire app cache (e.g. another runtime migration).
KEY_PREFIX = '3:'


def get(key, *args, **kwargs):
	return _memcache.get(KEY_PREFIX + key, *args, **kwargs)


def set(key, value, *args, **kwargs):
	return _memcache.set(KEY_PREFIX + key, value, *args, **kwargs)


def add(key, value, *args, **kwargs):
	return _memcache.add(KEY_PREFIX + key, value, *args, **kwargs)


def delete(key, *args, **kwargs):
	return _memcache.delete(KEY_PREFIX + key, *args, **kwargs)
