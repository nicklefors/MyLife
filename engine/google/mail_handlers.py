"""Facade for inbound mail handling.

``google.appengine.ext.webapp.mail_handlers`` does not exist on the python3
runtime, so the ``InboundMailHandler`` base class is reimplemented on top of
webapp2 and ``google.appengine.api.mail`` (which still provides
``InboundEmailMessage`` under bundled services).  Subclasses override
``receive(mail_message)`` exactly as before, and register via ``mapping()``.
"""
import webapp2
from google.appengine.api import mail


class InboundMailHandler(webapp2.RequestHandler):
    """webapp2 equivalent of the legacy bundled InboundMailHandler."""

    def receive(self, mail_message):
        """Override in subclasses to process the InboundEmailMessage."""
        raise NotImplementedError()

    def post(self):
        # App Engine delivers the raw MIME message as the request body to
        # /_ah/mail/<address>; parse it and hand off to receive().
        self.receive(mail.InboundEmailMessage(self.request.body))

    @classmethod
    def mapping(cls):
        """Route tuple for registration on a webapp2.WSGIApplication."""
        return ('/_ah/mail/.+', cls)
