"""
Facade for Google App Engine's NDB datastore.
Re-exports the ndb module and all utilities from datastore.py.
"""
# Import the ndb module itself to preserve structure
from engine.google.datastore import ndb

# Also re-export all items from datastore
from engine.google.datastore import *
