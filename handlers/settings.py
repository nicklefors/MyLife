import webapp2, filestore
from templates import get_template
from models.settings import Settings
from models.userimage import UserImage
from models.timezones import timezones
from models.migratetask import MigrateTask
from handlers import dropbox

class SettingsHandler(webapp2.RequestHandler):
	def get(self):

		#Check whether the migration is done so we can see whether to show the Blobstore Migration
		#or not...
		settings = Settings.get()

		if not settings.blobstore_migration_done:
			migration_task_finished = bool(MigrateTask.query(MigrateTask.status == 'finished').get())
			if migration_task_finished:
				settings.blobstore_migration_done = True
				settings.put()
			else:
				#Try to figure out whether this is a new user that has nothing in the blobstore...
				if not UserImage.query().get():
					settings.blobstore_migration_done = True
					settings.put()

		self._render(settings)

	def post(self):
		settings = Settings.get()

		settings.email_address = self.request.get('email-address')
		settings.timezone = self.request.get('timezone')
		settings.email_hour = int(self.request.get('email-hour'))
		settings.include_old_post_in_entry = self.request.get('include-old-entry') == 'yes'

		settings.dropbox_app_key = self.request.get('dropbox-app-key').strip()
		app_secret = self.request.get('dropbox-app-secret').strip()
		if app_secret:
			settings.dropbox_app_secret = app_secret
		settings.put()

		#If the user pasted an authorization code, exchange it for a refresh token.
		dropbox_message = None
		auth_code = self.request.get('dropbox-auth-code').strip()
		if auth_code:
			try:
				dropbox.exchange_code(settings, auth_code)
				dropbox_message = 'Connected to Dropbox successfully.'
			except Exception as ex:
				dropbox_message = 'Failed to connect to Dropbox: %s' % ex

		self._render(settings, True, dropbox_message)

	def _render(self, settings, saved=False, dropbox_message=None):
		authorize_url = ''
		if settings.dropbox_app_key:
			authorize_url = ('https://www.dropbox.com/oauth2/authorize?client_id=%s'
				'&response_type=code&token_access_type=offline' % settings.dropbox_app_key)

		data = {
			"page" : "settings",
			"email_address" : settings.email_address,
			"dropbox_app_key" : settings.dropbox_app_key or "",
			"dropbox_secret_set" : bool(settings.dropbox_app_secret),
			"dropbox_connected" : bool(settings.dropbox_refresh_token),
			"dropbox_last_backup" : settings.dropbox_last_backup,
			"dropbox_authorize_url" : authorize_url,
			"dropbox_message" : dropbox_message,
			"timezone" : settings.timezone,
			"timezones" : timezones,
			"email_hour" : settings.email_hour,
			"include_old_post_in_entry" : settings.include_old_post_in_entry,
			"upload_url" : filestore.create_upload_url('/upload-finished'),
			"saved" : saved,
			"can_migrate_images" : not settings.blobstore_migration_done,
			"bucket_exists" : filestore.bucket_exists(),
			"version" : open('VERSION').read()
		}
		self.response.write(get_template('settings.html').render(data))
