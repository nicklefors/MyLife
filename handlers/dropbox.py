from google.appengine.runtime import apiproxy_errors
from models.post import Post
from models.settings import Settings
from models.userimage import UserImage
import logging, traceback, webapp2, json, datetime, filestore, io
import requests
from errorhandling import log_error

DROPBOX_TOKEN_URL = 'https://api.dropboxapi.com/oauth2/token'


def _apply_token_response(settings, data):
	"""Persist an /oauth2/token response onto the Settings entity (caller puts())."""
	settings.dropbox_access_token = data['access_token']
	expires_in = data.get('expires_in', 14400)
	settings.dropbox_access_token_expires = datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
	if data.get('refresh_token'):
		settings.dropbox_refresh_token = data['refresh_token']


def exchange_code(settings, code):
	"""Exchange a one-time authorization code for a refresh token + access token."""
	resp = requests.post(DROPBOX_TOKEN_URL, data={
		'grant_type': 'authorization_code',
		'code': code,
		'client_id': settings.dropbox_app_key,
		'client_secret': settings.dropbox_app_secret,
	})
	if resp.status_code != 200:
		raise Exception('Dropbox code exchange failed. Status: %s, body: %s' % (resp.status_code, resp.text))
	_apply_token_response(settings, resp.json())
	settings.put()


def get_access_token(settings):
	"""Return a usable Dropbox bearer token.

	Refresh mode (refresh token + app key/secret present): reuse the cached
	short-lived access token while it is still valid, otherwise mint a new one
	with the refresh token. Legacy mode: return the stored long-lived token.
	"""
	if settings.dropbox_refresh_token and settings.dropbox_app_key and settings.dropbox_app_secret:
		now = datetime.datetime.now()
		if (settings.dropbox_access_token and settings.dropbox_access_token_expires
				and settings.dropbox_access_token_expires > now + datetime.timedelta(minutes=5)):
			return settings.dropbox_access_token
		resp = requests.post(DROPBOX_TOKEN_URL, data={
			'grant_type': 'refresh_token',
			'refresh_token': settings.dropbox_refresh_token,
			'client_id': settings.dropbox_app_key,
			'client_secret': settings.dropbox_app_secret,
		})
		if resp.status_code != 200:
			raise Exception('Dropbox token refresh failed. Status: %s, body: %s' % (resp.status_code, resp.text))
		_apply_token_response(settings, resp.json())
		settings.put()
		return settings.dropbox_access_token
	return settings.dropbox_access_token


class DropboxBackupHandler(webapp2.RequestHandler):
	def get(self):
		images_total = 0
		images_backed_up = 0
		try:
			self.response.headers['Content-Type'] = 'text/plain'
			settings = Settings.get()

			if not (settings.dropbox_refresh_token or settings.dropbox_access_token):
				self.log('No Dropbox credentials configured, no backup will be performed.')
				return

			access_token = get_access_token(settings)


			posts = [p for p in Post.query().order(Post.date).fetch()]

			self.log('Backing up %s posts to Dropbox' % len(posts))
			post_text = io.StringIO()
			for p in posts:
				post_text.write(p.date.strftime('%Y-%m-%d'))
				post_text.write('\r\n\r\n')
				post_text.write(p.text.replace('\r\n', '\n').replace('\n', '\r\n').rstrip())
				post_text.write('\r\n\r\n')

			result = self.put_file(access_token, 'MyLife.txt', post_text.getvalue().encode('utf-8'))
			post_text.close()
			self.log('Backed up posts. Revision: %s' % result['rev'])

			self.log('Fetching Dropbox file list')
			
			files_in_dropbox = self.get_dropbox_filelist(access_token)
			
			self.log('Got %s files from Dropbox' % len(files_in_dropbox))

			self.log('Fetching images...')
			images = [i for i in UserImage.query().order(UserImage.date).fetch()]

			self.log('Total images in MyLife: %s' % len(images))

			not_backed_up = [i for i in images if not i.backed_up_in_dropbox]
			not_in_dropbox = [i for i in images if not i.filename in files_in_dropbox]

			self.log('\nFiles not backed up: \n\n' + '\n'.join([i.filename for i in not_backed_up]))
			self.log('\nFiles marked as backed up, but not in Dropbox: \n\n' + '\n'.join([i.filename for i in not_in_dropbox]))

			images = not_backed_up + not_in_dropbox

			images_total = len(images)
			self.log('Found %s images that need to be backed up in Dropbox' % images_total)
			for img in images:
				self.log('Backing up %s' % img.filename)
				bytes = filestore.read(img.original_size_key)
				result = self.put_file(access_token, img.filename, bytes)
				self.log('Backed up %s. Revision: %s' % (img.filename, result['rev']))
				img.backed_up_in_dropbox = True
				img.put()
				images_backed_up += 1


			settings.dropbox_last_backup = datetime.datetime.now()
			settings.put()
			self.log('Finished backup successfully')
		except apiproxy_errors.OverQuotaError as ex:
			self.log(ex)
			log_error('Error backing up to Dropbox, quota exceeded', 'The backup operation did not complete because it ran out of quota. ' +
				'The next time it runs it will continue backing up your posts and images.' +
				'%s images out of %s were backed up before failing' % (images_backed_up, images_total))
		except Exception as ex:
			self.log('Failed to backup posts and images to dropbox: %s' % traceback.format_exc(6))
			logging.exception("message")
			self.log('ERROR: %s' % ex)
			log_error('Error backing up to Dropbox', 'Failed to backup posts and images to dropbox: %s' % traceback.format_exc(6))


	def log(self, msg):
		self.response.write(str(msg) + '\r\n')
		logging.info(msg)

	def get_file_info(self, access_token, name):

		headers = {
			'Content-Type' : 'application/json',
			'Authorization' : 'Bearer ' + access_token
		}

		data = {
    		"path": "/" + name,
		    "include_media_info": False,
		    "include_deleted": False,
		    "include_has_explicit_shared_members": False
		}

		result = requests.post(
			'https://api.dropboxapi.com/2/files/get_metadata',
			data=json.dumps(data),
			headers=headers
		)

		if result.status_code != 200:
			raise Exception("Failed to get file metadata from Dropbox. Status: %s, body: %s" % (result.status_code, result.text))
		self.log(result.text)
		return result.json()


	def put_file(self, access_token, name, bytes):

#		info = self.get_file_info(access_token, name)
#		self.log(info)

		dropbox_args = {
    		"path": "/" + name,
    		"mode": { ".tag" : "overwrite"},
    		"autorename": True,
    		"mute": False
		}

		headers = {
			'Content-Type' : 'application/octet-stream',
			'Authorization' : 'Bearer ' + access_token,
			'Dropbox-API-Arg' : json.dumps(dropbox_args)
		}

		result = requests.post(
			'https://content.dropboxapi.com/2/files/upload',
			data=bytes,
			headers=headers
		)

		if result.status_code != 200:
			self.log(result.text)
			raise Exception("Failed to send file to Dropbox. Status: %s, body: %s" % (result.status_code, result.text))
		return result.json()


	def get_dropbox_filelist(self, access_token):
		headers = {
			'Content-Type' : 'application/json',
			'Authorization' : 'Bearer ' + access_token
		}

		data = {
			"path": "",
			"recursive": True,
			"include_media_info": False,
			"include_deleted": False,
			"include_has_explicit_shared_members": False,
			"include_mounted_folders": False,
			"limit" : 1000
		}

		result = requests.post(
			'https://api.dropboxapi.com/2/files/list_folder',
			data=json.dumps(data),
			headers=headers)

		if result.status_code != 200:
			raise Exception("Failed to get files from Dropbox. Status: %s, body: %s" % (result.status_code, result.text))

		json_data = result.json()
		file_list = [o['name'] for o in json_data['entries']]

		#Get everything
		while json_data['has_more']:
			self.log('Getting next batch...')
			result = requests.post(
				'https://api.dropboxapi.com/2/files/list_folder/continue',
				data=json.dumps({"cursor" : json_data['cursor']}),
				headers=headers)

			if result.status_code != 200:
				raise Exception("Failed to get files from Dropbox. Status: %s, body: %s" % (result.status_code, result.text))

			json_data = result.json()
			file_list.extend([o['name'] for o in json_data['entries']])

		return file_list

