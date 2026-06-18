"""
Engine module for CMS.

This module provides a facade pattern for Google App Engine services,
centralizing all GAE imports and enabling easier testing and future migration.

Usage:
    from engine.google import ndb, db, memcache, taskqueue
    from engine.environment import ON_LOCALHOST, ON_TEST_SERVER
"""

# This file intentionally left empty to allow imports from submodules
