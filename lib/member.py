import base64
import pickle
import time
from lib import rhapapi

class Member():
	def __init__(self):
		self.info = []
		self.filename = None
		self.picklefile = ''
		self.cobrandId = "40134"
		self.user_info = {}
		self.username = ""
		self.password = ""
		self.access_token = ""
		self.refresh_token = ""
		self.issued_at = ""
		self.expires_in = ""
		self.guid = ""
		self.account_type = "Not available"
		self.date_created = "Not available"
		self.first_name = ""
		self.last_name = ""
		self.catalog = ""
		self.timestamp = ""

	def set_addon_path(self, path):
		self.filename = path+'/resources/.rhapuser.obj'

	def has_saved_creds(self):
		print "checking saved creds"
		try:
			self.user_info = pickle.load(open(self.filename, 'rb'))
			print "Using saved user credentials for "+self.user_info['username']
			#prettyprint(self.user_info)
			self.username = self.user_info['username']
			self.password = base64.b64decode(self.user_info['password'])
			self.guid = self.user_info['guid']
			self.access_token = self.user_info['access_token']
			self.refresh_token = self.user_info['refresh_token']
			self.issued_at = self.user_info['issued_at']
			self.expires_in = self.user_info['expires_in']
			self.first_name = self.user_info['first_name']
			self.last_name = self.user_info['last_name']
			self.catalog = self.user_info['catalog']
			self.timestamp = self.user_info['timestamp']
		except:
			print "Couldn't read saved user data. Login please"
			return False
		diff = time.time()-self.timestamp
		if diff < self.expires_in:
			print "Saved creds look good. Automatic login successful!"
			return True
		else:
			print "Saved creds have expired. Generating new ones."
			self.login_member(self.username, self.password)
			return True

	def save_user_info(self):
		#print "Adding data to user_info object"
		self.user_info['username'] = self.username
		self.user_info['password'] = base64.b64encode(self.password)
		self.user_info['guid'] = self.guid
		self.user_info['access_token'] = self.access_token
		self.user_info['refresh_token'] = self.refresh_token
		self.user_info['issued_at'] = self.issued_at
		self.user_info['expires_in'] = self.expires_in
		self.user_info['first_name'] = self.first_name
		self.user_info['last_name'] = self.last_name
		self.user_info['catalog'] = self.catalog
		self.user_info['timestamp'] = time.time()
		#prettyprint(self.user_info)
		print "Saving userdata..."
		pickle.dump(self.user_info, open(self.filename, 'wb'))
		#print "Userdata saved!"


	def login_member(self, name, pswd):
		print "attempting login..."
		data = {}
		self.username = name
		self.password = pswd
		api = rhapapi.Api()
		result = api.login_member(name, pswd)
		if result:
			self.access_token =     result["access_token"]
			self.catalog =          result["catalog"]
			self.expires_in =       result["expires_in"]
			self.first_name =       result["first_name"]
			self.guid =             result["guid"]
			self.issued_at =        result["issued_at"]
			self.last_name =        result["last_name"]
			self.refresh_token =    result["refresh_token"]
			data['logged_in'] = True
			data['bad_creds'] = False
			self.save_user_info()
			return data
		else:
			print "login failed"
			data['logged_in'] = False
			data['bad_creds'] = True
			return data