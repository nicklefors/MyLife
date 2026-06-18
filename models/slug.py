import datetime
from engine.google import ndb


class Slug(ndb.Model):
	slug = ndb.StringProperty()
	date = ndb.DateProperty()
	created = ndb.DateTimeProperty(auto_now_add=True)
