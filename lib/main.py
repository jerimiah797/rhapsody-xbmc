import xbmcaddon
from lib import rhapapi
from lib import image
from lib import member
from lib import play
from lib import view
from lib import lists
from lib import caching



class Application():
	__vars = None


	def __init__(self):
		self.__vars = {}  #dict for app vars
		self.view_keeper = {'browseview': 'browse_newreleases', 'frame': 'Browse', 'view_id':3350}

		self.__addon_id__ = 'script.audio.rhapsody'
		self.__addon_cfg__ = xbmcaddon.Addon(self.__addon_id__)
		self.__addon_path__ = self.__addon_cfg__.getAddonInfo('path')
		self.__addon_version__ = self.__addon_cfg__.getAddonInfo('version')
		self.__addon_icon__ = self.__addon_cfg__.getAddonInfo('icon')

		self.newreleases =   None
		self.topalbums =     None
		self.topartists =    None
		self.toptracks =     None
		self.lib_albums =    None
		self.lib_artists =   None
		self.windowtracklist = None

		self.player = None
		self.playlist = None

		self.mem = member.Member(self)
		self.api = rhapapi.Api()
		self.cache = caching.Cache(self)
		self.img = image.Image(self.__addon_path__)
		self.win = view.MainWin("main.xml", self.__addon_path__, 'Default', '720p', app=self)

		self.init_lists()
		self.init_vars()

		self.player = play.Player(app=self)
		self.playlist = self.player.playlist
		self.win.toptracks = self.toptracks
		self.win.player = self.player
		self.win.playlist = self.playlist

	def init_lists(self):
		self.newreleases =   lists.ContentList('album',   'newreleases',   self.__addon_path__+'/resources/.newreleases.obj', self)
		self.topalbums =     lists.ContentList('album',   'topalbums',     self.__addon_path__+'/resources/.topalbums.obj', self)
		self.topartists =    lists.ContentList('artist',  'topartists',    self.__addon_path__+'/resources/.topartists.obj', self)
		self.toptracks =     lists.ContentList('track',   'toptracks',     self.__addon_path__+'/resources/.toptracks.obj', self)
		self.lib_albums =    lists.ContentList('album',   'lib_albums',    self.__addon_path__+'/resources/.lib_albums.obj', self)
		self.lib_artists =   lists.ContentList('artist',  'lib_artists',   self.__addon_path__+'/resources/.lib_artists.obj', self)
		#lib_tracks =    ContentList('track',   'lib_tracks',    __addon_path__+'/resources/.lib_tracks.obj')
		#lib_stations =  ContentList('station', 'lib_stations',  __addon_path__+'/resources/.lib_stations.obj')
		#lib_favorites = ContentList('tracks',  'lib_favorites', __addon_path__+'/resources/.lib_favorites.obj')
		self.windowtracklist = lists.WindowTrackList()

	def init_vars(self):
		self.set_var('view_matrix' , {"browse_newreleases": self.newreleases,
						                "browse_topalbums":   self.topalbums,
						                "browse_topartists":  self.topartists,
						                "browse_toptracks":   self.toptracks,
						                "library_albums":     self.lib_albums,
						                "library_artists":    self.lib_artists,
						                #"library_tracks":     lib_tracks,
						                #"library_stations":   lib_stations,
						                #"library_favorites":  lib_favorites,
						                })

		self.set_var('list_matrix' , {"browse_newreleases":    3350,
						              "browse_topalbums":      3351,
						              "browse_topartists":     3352,
						              "browse_toptracks":      3353,
						              "library_albums":        3550,
						              "library_artists":       3551,
						                })

		self.set_var('running', True)
		self.set_var('logged_in', False)
		self.set_var('bad_creds', False)
		self.set_var('last_rendered_list', None)




	def set_var(self, name, value):
		self.__vars[name] = value


	def has_var(self, name):
		return name in self.__vars


	def get_var(self, name):
		return self.__vars[name]


	def remove_var(self, name):
		del self.__vars[name]
