import os


def get_application_id():
	# Resolve the project id across runtimes:
	# - GOOGLE_CLOUD_PROJECT: gen2 (py3) runtimes, already unprefixed ('matterhackers')
	# - GAE_APPLICATION: gen2 fallback, partition-prefixed ('s~matterhackers')
	# - APPLICATION_ID: gen1 (py27) runtime, partition-prefixed ('s~matterhackers')
	# The gen1 runtime does not set GOOGLE_CLOUD_PROJECT, so without the fallbacks
	# py2 prod resolves to None (which engine.environment must never treat as a
	# test server -- that would silently disable permission checks).
	app_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
	if not app_id:
		app_id = os.environ.get('GAE_APPLICATION') or os.environ.get('APPLICATION_ID')
		if app_id and '~' in app_id:
			app_id = app_id.split('~', 1)[1]  # strip the 's~'/'e~' partition prefix
	return app_id


def get_application_is_local():
	# On the py3 dev_appserver, gunicorn overwrites SERVER_SOFTWARE to
	# 'gunicorn/<ver>' at worker boot, defeating the legacy
	# SERVER_SOFTWARE.startswith('Development') check. GAE_ENV is set to
	# 'localdev' by dev_appserver and 'standard' on real GAE, and gunicorn
	# does not touch it, so it is the reliable local signal. Keep the legacy
	# check as a fallback for the py2 runtime.
	if os.getenv('GAE_ENV', '') == 'localdev':
		return True
	return os.getenv('SERVER_SOFTWARE', '').startswith('Development')
