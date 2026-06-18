# get_application_is_local lives in identity (the lower-level module) so there is
# a single definition of the local-env signal; re-exported here for callers that
# import it from engine.environment.
from engine.google.identity import get_application_id, get_application_is_local


def get_application_is_test_server():
    application_id = get_application_id()
    if not application_id:
        # No resolvable project id only happens off GAE: identity.get_application_id
        # falls back through GOOGLE_CLOUD_PROJECT / GAE_APPLICATION / APPLICATION_ID,
        # so both gen1 (py2) and gen2 (py3) prod always resolve one. For an
        # unidentified process, refuse to guess: treating it as test silently
        # disables permission checks (base_handler.user_has_role short-circuits on
        # ON_TEST_SERVER -- this happened on py2 prod, which had no
        # GOOGLE_CLOUD_PROJECT), and treating it as prod lets stray local tooling
        # hit prod services (service_urls/api_* fall through to prod endpoints and
        # credentials). The raise fires at import time via ON_TEST_SERVER below --
        # intentional, so a misconfigured process fails fast and loud. dev_appserver
        # sets GAE_ENV=localdev automatically; other off-GAE tooling must set it.
        if get_application_is_local():
            return True
        raise RuntimeError(
            'Cannot determine environment: no resolvable project id '
            '(GOOGLE_CLOUD_PROJECT / GAE_APPLICATION / APPLICATION_ID) '
            'and not local. Off-GAE processes must set GAE_ENV=localdev.')
    return application_id == 'matterhackers-test'


# Module-level constants
ON_LOCALHOST = get_application_is_local()
ON_TEST_SERVER = get_application_is_test_server()
APPLICATION_ID = get_application_id()
APPENGINE = True  # Always True when using engine wrapper