"""
Facade for Google App Engine's Blobstore service.

On python3 the blobstore download/upload handler base classes moved from
``google.appengine.ext.webapp.blobstore_handlers`` into
``google.appengine.ext.blobstore`` itself.
"""
from google.appengine.ext.blobstore import *

# py2-signature compat subclasses (webapp2 handlers; send_blob writes to
# self.response, get_uploads/get_file_infos take no environ).
from engine.google.blobstore_handlers import (
    BlobstoreDownloadHandler,
    BlobstoreUploadHandler,
)
