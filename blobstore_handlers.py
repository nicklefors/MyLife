"""Python 3 compatibility shim for the blobstore handler base classes.

On the python3 runtime ``google.appengine.ext.webapp.blobstore_handlers`` no
longer exists; the base classes now live in ``google.appengine.ext.blobstore``
(appengine-python-standard) and changed contract in two ways this restores to
the py2 calling convention:

1. They are plain classes, not webapp RequestHandlers. webapp2 instantiates
   handlers as ``handler(request, response)``, so mixing ``webapp2.RequestHandler``
   back in restores ``self.request`` / ``self.response`` / ``dispatch``.
2. Their methods take the WSGI ``environ`` as a new first argument and
   ``send_blob`` returns a headers dict instead of writing to the response. The
   overrides below pass ``self.request.environ`` through and apply the returned
   headers to ``self.response``.
"""
import webapp2

from google.appengine.ext.blobstore import BlobstoreDownloadHandler as _BlobstoreDownloadHandler
from google.appengine.ext.blobstore import BlobstoreUploadHandler as _BlobstoreUploadHandler


class BlobstoreDownloadHandler(webapp2.RequestHandler, _BlobstoreDownloadHandler):
	def send_blob(self, blob_key_or_info, content_type=None, save_as=None, start=None, end=None, **kwargs):
		headers = _BlobstoreDownloadHandler.send_blob(self, self.request.environ, blob_key_or_info,
			content_type=content_type, save_as=save_as, start=start, end=end, **kwargs)
		for key, value in headers.items():
			if isinstance(value, bytes):
				value = value.decode('utf-8')
			if not value.isascii():
				# gunicorn rejects non-ascii header values (e.g. a unicode filename
				# in the Content-Disposition fallback); strip them. Browsers prefer
				# the percent-encoded filename* part anyway (RFC 6266).
				value = value.encode('ascii', 'ignore').decode('ascii')
			self.response.headers[key] = value


class BlobstoreUploadHandler(webapp2.RequestHandler, _BlobstoreUploadHandler):
	def __init__(self, request=None, response=None):
		_BlobstoreUploadHandler.__init__(self)  # initializes the upload/file-info caches
		webapp2.RequestHandler.__init__(self, request, response)

	def _rewound_environ(self):
		# The py3 implementations parse environ['wsgi.input'] directly, but the
		# stream is left at EOF once webob reads it (e.g. self.request.get(...)).
		# Make the body seekable and rewind so the full multipart body is visible
		# to the blobstore parser.
		self.request.make_body_seekable()
		environ = self.request.environ
		environ['wsgi.input'].seek(0)
		return environ

	def get_uploads(self, field_name=None):
		return _BlobstoreUploadHandler.get_uploads(self, self._rewound_environ(), field_name)

	def get_file_infos(self, field_name=None):
		return _BlobstoreUploadHandler.get_file_infos(self, self._rewound_environ(), field_name)
