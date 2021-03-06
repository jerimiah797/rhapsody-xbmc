import xbmcgui
import xbmc
import xbmcvfs

import os
import subprocess
import thread
import threading
from threading import Thread
from lib import utils

def draw_mainwin(win, app, **kwargs):
	if kwargs.get("results"):
		results = kwargs.get("results")
	else:
		results = None
	frame = win.handle.getProperty('frame')
	if frame == "Settings":
		#print "Drawmain: No lists to draw on settings Page"
		win.handle.setFocusId(1001)
	elif (frame == "Search") and (win.search_ever_used == False):
		print "drawmainwin - skipping all that and focusing 402"
		win.handle.setFocusId(402)
	else:
		print "Performing draw_mainwin"
		print "Search submitted: "+str(win.search_submitted)
		view = win.handle.getProperty('browseview')
		list_instance = app.get_var('view_matrix')[view]
		if win.search_submitted == True:
			list_instance.fresh = False
		win.list_id = app.get_var('list_matrix')[win.getProperty('browseview')]
		win.clist = win.getControl(win.list_id)
		print "Drawmainwin: view: %s list instance: %s list id: %s" % (view, list_instance.name, str(win.list_id))
		win.make_visible(300, win.list_id)
		list_instance.make_active(results=results)
		if (win.search_submitted == False) and (frame == "Search"):
			win.handle.setFocusId(402)
			print "skipped setting focus on content list"
		else:
			win.setFocusId(win.list_id)
		if list_instance.pos:
			print "List position: "+str(list_instance.pos)
			win.clist.selectItem(list_instance.pos)
		win.search_submitted = False
		for index in range(win.clist.size()):
			li = win.clist.getListItem(index)
			if list_instance.type == "album":
				url = li.getProperty('thumb_url')
				thread.start_new_thread(load_album_thumb, (li, app, url))
			elif list_instance.type == "artist":
				artist_id = li.getProperty('artist_id')
				if not artist_id in app.cache.artist:
					if artist_id == 'Art.0':
						#print "detected artist 0 case!"
						url = app.img.default_artist_img
						genre = ""
					else:
						thread.start_new_thread(load_artist_thumb, (li, artist_id, app))
						thread.start_new_thread(load_artist_genre, (li, artist_id, app))	
				else:
					if artist_id == 'Art.0':
						#print "detected artist 0 case!"
						url = app.img.default_artist_img
						genre = ""
					else:
						thread.start_new_thread(get_artist_image_from_cache, (li, artist_id, app))
						thread.start_new_thread(get_artist_genre_from_cache, (li, artist_id, app))
		#elif frame == "Search":
		#	print "drawmainwin - skipping all that and focusing 201"
		#	win.handle.setFocusId(201)
			
#threadsafe wrapper for fetching and loading album thumbs 
def load_album_thumb(li, app, url):
	li.setThumbnailImage(os.path.join(app.__addon_data__, app.img.handler(url, 'small', 'album')))

#threadsafe wrapper for image loading
def get_artist_image_from_cache(li, artist_id, app):
	if len(app.cache.artist[artist_id]['thumb_url']) > 5:
		url = app.cache.artist[artist_id]['thumb_url']
		li.setThumbnailImage(os.path.join(app.__addon_data__, app.img.handler(url, 'small', 'artist')))
	else:
		url = app.img.identify_artist_thumb(artist_id)
		if url:
			app.cache.artist[artist_id]['thumb_url'] = url
			li.setThumbnailImage(os.path.join(app.__addon_data__, app.img.handler(url, 'small', 'artist')))

def get_artist_genre_from_cache(li, artist_id, app):
	if app.cache.artist[artist_id]['style']:
		li.setLabel2(app.cache.artist[artist_id]['style'])
	else:
		g_id = app.api.get_artist_genre(artist_id)
		if g_id:
			if not (g_id in app.cache.genre_dict__):
				results = app.api.get_genre_detail(g_id)
				app.cache.genre_dict__[g_id] = results["name"]
				app.cache.genre_modified = True
				print "** Added missing genre "+g_id+" to genre cache ** "+results["name"]
			li.setLabel2(app.cache.genre_dict__[g_id])
			app.cache.artist[artist_id]['style'] = app.cache.genre_dict__[g_id]


def load_artist_thumb(li, artist_id, app):
	url = app.img.identify_artist_thumb(artist_id)
	if url:
		app.cache.artist[artist_id]['thumb_url'] = url
		li.setThumbnailImage(os.path.join(app.__addon_data__, app.img.handler(url, 'small', 'artist')))

def load_artist_genre(li, artist_id, app):
	g_id = app.api.get_artist_genre(artist_id)
	if g_id:
		li.setLabel2(app.cache.genre_dict__[g_id])
		app.cache.artist[artist_id]['style'] = app.cache.genre_dict__[g_id]


def draw_playlist_sublist(win, app, thing):
	#print "Draw playlist_sublist"

	cache = app.cache.playlist
	win.dlist = win.getControl(3651)
	win.dlist.reset()
	if win.manage_playlist_detail(app.cache.playlist, thing, thing['playlist_id']):
		#win.dlist = win.getControl(3651)
		#win.dlist.reset()
		liz = app.windowtracklist.get_playlist_litems(cache, thing['playlist_id'])
		for item in liz:
			win.dlist.addItem(item)
		###win.sync_playlist_pos()
		#win.make_visible(3651)
	else:
		#print "resetting list"
		win.dlist.reset()
	win.make_visible(3651)



class WinBase(xbmcgui.WindowXML):
	def __init__(self, xmlName, thescriptPath, defaultname, forceFallback):
		#print "I'm the MainWin base dialog class"
		pass


class LoginWin(WinBase):
	def __init__(self, *args, **kwargs):
		WinBase.__init__(self, *args)
		self.app = kwargs.get('app')
		self.mem = self.app.mem

	def onInit(self):
		#print "Starting login UI loop"
		while not self.app.get_var('logged_in'):
			if self.app.get_var('bad_creds'):
				self.getControl(10).setLabel('Login failed! Try again...')
				#print "Set fail label message"
			self.inputwin = InputDialog("input.xml", self.app.__addon_path__, 'Default', '720p', app=self.app)
			self.inputwin.doModal()
			if not self.app.get_var('exiting'):
				data = self.mem.login_member(self.inputwin.name_txt, self.inputwin.pswd_txt)
				self.app.set_var('logged_in', data['logged_in'])
				self.app.set_var('bad_creds', data['bad_creds'])
				del self.inputwin
			#print "Logged_in value: " + str(self.app.get_var('logged_in'))
			#print "Bad Creds value: " + str(self.app.get_var('bad_creds'))
			else:
				break

		#print "Exited the login UI loop! Calling the del function"
		self.close()


class DialogBase(xbmcgui.WindowXMLDialog):
	def __init__(self, xmlName, thescriptPath, defaultname, forceFallback):
		#print "I'm the Dialog base dialog class"
		pass


class InputDialog(DialogBase):

	#def __init__(self, xmlFilename, scriptPath, defaultSkin, defaultRes):
	def __init__(self, *args, **kwargs):
		DialogBase.__init__(self, *args)
		self.app = kwargs.get('app')
		self.name = xbmcgui.ControlEdit(530, 320, 400, 120, '', 'rhapsody_font16', '0xDD171717', focusTexture="none.png")
		self.pswd = xbmcgui.ControlEdit(530, 320, 400, 120, '', font='rhapsody_font16', textColor='0xDD171717', focusTexture="none.png", isPassword=1)
		self.butn = None
		self.name_txt = ""
		self.pswd_txt = ""

	def onInit(self):
		self.name_select = self.getControl(10)
		self.pswd_select = self.getControl(11)
		self.pswd_select.setVisible(False)
		self.addControl(self.name)
		self.addControl(self.pswd)
		self.butn = self.getControl(22)
		self.name.setPosition(600, 320)
		self.name.setWidth(400)
		self.name.controlDown(self.pswd)
		self.pswd.setPosition(600, 410)
		self.pswd.setWidth(400)
		self.pswd.controlUp(self.name)
		self.pswd.controlDown(self.butn)
		self.butn.controlUp(self.pswd)
		self.setFocus(self.name)


	def onAction(self, action):
		#print str(action.getId())
		#print type(action)
		if action.getId() == 7:
			if self.getFocus() == self.name:
				self.setFocus(self.pswd)
			elif self.getFocus() == self.pswd:
				self.setFocus(self.butn)
			elif self.getFocusId() == 22:
				self.app.set_var('exiting', False)
				self.close()
				self.name_txt = self.name.getText()
				self.pswd_txt = self.pswd.getText()
			else: pass
		elif action.getId() == 18:
			if self.getFocus() == self.name:
				self.setFocus(self.pswd)
			elif self.getFocus() == self.pswd:
				self.setFocus(self.butn)
			elif self.getFocus() == self.butn:
				self.setFocus(self.name)
			else: pass
		elif action.getId() == 10:
			print "ID 10 key - ESC"
			self.app.set_var('exiting', True)
			self.close()
			utils.goodbye_while_logged_out(self.app)
		#elif action.getId() == 92:
		#	self.app.set_var('exiting', True)
		#	self.close()
		#	utils.goodbye_while_logged_out(self.app)
		else:
			pass

	def onFocus(self, control):
		if control == 3001:
			self.name_select.setVisible(True)
			self.pswd_select.setVisible(False)
		elif control == 3002:
			self.name_select.setVisible(False)
			self.pswd_select.setVisible(True)
		elif control == 22:
			self.name_select.setVisible(False)
			self.pswd_select.setVisible(False)
		else: pass


class MainWin(WinBase):

	def __init__(self, *args, **kwargs):
		WinBase.__init__(self, *args)
		#print "running _init_ for mainwin"
		self.app = kwargs.get('app')
		self.mem = self.app.mem
		self.cache = self.app.cache
		self.img = self.app.img
		self.api = self.app.api
		self.player = self.app.player
		self.playlist = self.app.playlist
		self.setup = False
		self.list_id = None #main list xml id
		self.playlist_list_id = None #playlist tracks xml id
		self.handle = None
		self.frame_label = None
		self.clist = None #main list for active view
		self.dlist = None #list for playlist tracks view
		self.mem_playlist_selection = None
		self.search_strings = ["Artists", "Albums", "Tracks", "Broadcast Radio"]
		self.search_types = ["artist", "album", "track", "radio"]
		self.search_views = ["search_artists", "search_albums", "search_tracks", "search_broadcast"]
		self.search_types_index = 1
		self.selected_search_type = self.search_types[self.search_types_index]
		self.search_submitted = False
		self.search_ever_used = False
		print "Default search type: "+self.selected_search_type


	def onInit(self):
		#print "running onInit for mainwin"
		self.handle = xbmcgui.Window(xbmcgui.getCurrentWindowId())
		self.handle.setProperty("browseview", self.app.view_keeper['browseview'])
		self.handle.setProperty("frame", self.app.view_keeper['frame'])
		self.main()

	def main(self):

		self.handle.setProperty("full_name", self.mem.first_name+" "+self.mem.last_name)
		self.handle.setProperty("country", self.mem.catalog)
		self.handle.setProperty("logged_in", "true")
		self.handle.setProperty("username", self.mem.username)
		self.handle.setProperty("date_created", self.mem.date_created)
		self.handle.setProperty("account_type", self.mem.account_type)
		self.handle.setProperty("search_string", self.search_strings[self.search_types_index])
		self.frame_label = self.getControl(121)
		draw_mainwin(self, self.app)


	def onAction(self, action):

		if action.getId() == 7:		#enter/select
			self.manage_action(7)
		elif action.getId() == 3:    #up
			self.manage_action(3)
		elif action.getId() == 4:    #down
			self.manage_action(4)
		if action.getId() == 10:
			choice = True
			utils.goodbye(self.app, choice)
		elif action.getId() == 92:
			choice = True
			utils.goodbye(self.app, choice)
		else:
			pass


	def manage_action(self, id):

		if id == 3 or id == 4:

			if self.getFocusId() == 3650:
				#print "doing stuff since playlist list is focused"
				pos = self.clist.getSelectedPosition()
				if pos != self.mem_playlist_selection:
					self.mem_playlist_selection = self.clist.getSelectedPosition()
					thing = self.app.get_var('list')[self.mem_playlist_selection]
					draw_playlist_sublist(self, self.app, thing)
			else:
				pass

		if id == 7:

			if self.getFocusId() == 301 or self.getFocusId() == 501: # sliding panel on browse and library
				draw_mainwin(self, self.app)
				self.app.view_keeper = {'browseview': self.getProperty('browseview'), 'frame': self.getProperty('frame')}

			elif self.getFocusId() == 101: # left nav panel
				draw_mainwin(self, self.app)
				self.app.view_keeper = {'browseview': self.getProperty('browseview'), 'frame': self.getProperty('frame')}

			elif self.getFocusId() == 1001: # sign in with different account on settings page
				# Logout happens here
				self.app.set_var('logged_in', False)
				try:
					os.remove(self.mem.filename)
				except OSError, e:  ## if failed, report it back to the user ##
					print ("Error: %s - %s." % (e.filename,e.strerror))
				self.player.stop()
				self.playlist.clear()
				self.close()

			elif self.getFocusId() == 1002: # clear app data button on settings page
				path = "special://home/userdata/addon_data/script.audio.rhapsody/.clean_me"
				f = xbmcvfs.File(path, 'w')
				f.close()
				if xbmcvfs.exists("special://home/userdata/addon_data/script.audio.rhapsody/.clean_me"):
					w = xbmcgui.Dialog().ok("Success!!", "Rhapsody must restart now to finish deleting cache files")
					choice = False
					utils.goodbye(self.app, choice)

					# should pop a yes no dialog that deletes then quits instead of a notice
					print "Housekeeping trigger file created"
				else:
					print "Something went wrong creating housekeeping trigger file"

			elif self.getFocusId() == 401:  # new search button - opens keyboard dialog for text entry
				#self.app.mem.access_token = "sdlkfjlskdjf"
				#print "corrupted the access token for testing"
				kb = xbmc.Keyboard()
				kb.setHeading('Enter Artist, Album, Track, or Station') 
				kb.doModal()
				if (kb.isConfirmed()):
					text = kb.getText()
					print text
					results = self.app.api.get_search_results(text, self.selected_search_type)
					if results:
						#utils.prettyprint(results)
						print "got search results!"
						self.search_submitted = True
						self.search_ever_used = True
						print "set search_submitted to true"
						draw_mainwin(self, self.app, results=results)
						print "called draw_mainwin"

			elif self.getFocusId() == 402:
				print "OnAction happening for control 402"
				self.search_types_index = (self.search_types_index + 1) % 4
				self.selected_search_type = self.search_types[self.search_types_index]
				print "Search type changed to "+self.selected_search_type
				self.handle.setProperty("search_string", self.search_strings[self.search_types_index])
				self.handle.setProperty("browseview", self.search_views[self.search_types_index])
				draw_mainwin(self, self.app, results=None)

			#elif self.getFocusId() == 3651:
			#	print "OnAction: Lets play this playlist"







	def onClick(self, control):
		print "onClick detected! Control is "+str(control)
		try:
			pos = self.clist.getSelectedPosition()
			thing = self.app.get_var('list')[pos]
		except:
			print "onclick shouldn't be processed for empty lists"
			return
		#print "mainwin onClick: id: "+str(id)
		if (control == 3350) or (control == 3351) or (control == 3352) or (control == 3550) or (control == 3551) or (control == 3451):
			self.alb_dialog = AlbumDialog("album.xml", self.app.__addon_path__, 'Default', '720p', current_list=self.app.get_var('list'),
			                         pos=pos, cache=self.cache.album, alb_id=thing, app=self.app)
			self.alb_dialog.setProperty("review", "has_review")
			self.alb_dialog.doModal()
			self.alb_dialog.id = None
			if self.empty_list():
				draw_mainwin(self, self.app)
			self.clist.selectItem(self.alb_dialog.pos)
			#self.cache.save_album_data()

		elif control == 3353 or control == 3453 or control == 3950:
			self.start_playback(control)

		elif control == 3650:
			#self.manage_playlist_detail(thing['playlist_id'])
			pass

		elif control == 3651:
			print "Tring to play playlist"				
			#thing = self.app.get_var('list')[pos]
			self.start_playback(control)


	def start_playback(self, id):

		view = self.handle.getProperty('browseview')
		list_instance = self.app.get_var('view_matrix')[view]
		print list_instance.name
		#utils.prettyprint(list_instance.data[self.mem_playlist_selection])
		if id == 3651:  #attempting to play member playlist
			self.player.now_playing = {'pos': 0, 'type':'playlist', 'item':list_instance.data[self.mem_playlist_selection]['tracks'], 'id':list_instance.name}
		else:
			self.player.now_playing = {'pos': 0, 'type':'playlist', 'item':list_instance.data, 'id':list_instance.name}  #['data']}
		self.player.build()
		if id == 3353 or id == 3453 or id == 3950:
			self.player.now_playing['pos'] = self.clist.getSelectedPosition()
		elif id == 3651:
			self.player.now_playing['pos'] = self.dlist.getSelectedPosition()
		#xbmc.executebuiltin("XBMC.Notification(Rhapsody, Fetching song..., 5000, %s)" %(self.app.__addon_icon__))
		#track = self.player.add_playable_track(0)
		#if not track:
		#	xbmc.executebuiltin("XBMC.Notification(Rhapsody, Problem with this song. Aborting..., 2000, %s)" %(self.app.__addon_icon__))
		#	print "Unplayable track. Can't play this track"
		#	#player.stop()
		#	return False
		#self.player.get_session()
		thread.start_new_thread(self.app.player.get_session, () )
		self.player.playselected(self.player.now_playing['pos'])
		#xbmc.executebuiltin("XBMC.Notification(Rhapsody, Playback started, 2000, %s)" %(self.app.__addon_icon__))
		if id == 21:
			self.clist.selectItem(self.playlist.getposition())
			self.setFocusId(3353)


	def onFocus(self, control):
		#print("onfocus(): control %i" % control)
		if self.getFocusId() == 3650:
			#print "doing stuff since playlist list is focused"
			pos = self.clist.getSelectedPosition()
			if pos != self.mem_playlist_selection:
				self.mem_playlist_selection = self.clist.getSelectedPosition()
				thing = self.app.get_var('list')[self.mem_playlist_selection]
				draw_playlist_sublist(self, self.app, thing)


	def make_visible(self, *args):
		for item in args:
			self.getControl(item).setVisible(True)


	def empty_list(self):
		if self.clist.size() < 2:
			#print "window list is empty.. redrawing"
			return True


	def sync_playlist_pos(self):
		try:
			if self.player.now_playing['id'] == 'toptracks':
				print "syncing playlist pos because player.now_playing id is 'toptracks'"
				self.clist.selectItem(self.playlist.getposition())
				self.toptracks.pos = self.playlist.getposition()
			elif self.player.now_playing['id'] == self.alb_dialog.id:
				print "syncing playlist pos because player.now_player id is current album id"
				self.alb_dialog.clist.selectItem(self.playlist.getposition())
			elif self.player.now_playing['id'] == 'playlist':
				print "syncing playlist pos because player.now_playing id is 'playlist'"
				self.dlist.selectItem(self.playlist.getposition())
				self.toptracks.pos = self.playlist.getposition()
		except:
			print "Didn't need to sync playlist position"
			pass



	def manage_playlist_detail(self, cache, playlist, pl_id):
		#alb_id = playlist["album_id"]
		if playlist["tracks"] == {}:
			# try to get info from cached album data
			if cache.has_key(pl_id) and (cache[pl_id]['tracks'] != {}):
				print "Using tracklist from cached album data"
				return True
			else:
				print "Getting playlist tracklist from Rhapsody"
				results = self.api.get_playlist_details(pl_id)
				if results:
					#playlist["label"] = results["label"]
					playlist["tracks"] = results
					#playlist["style"] = results["primaryStyle"]
					return True
				else:
					print "Playlist contains no tracks!"
					return False
		else:
			print "Using playlist tracks from data in memory"
			return True




class AlbumDialog(DialogBase):

	def __init__(self, *args, **kwargs):
		DialogBase.__init__(self, *args)
		self.current_list = kwargs.get('current_list')
		self.cache = kwargs.get('cache')
		self.id = kwargs.get('alb_id')
		self.pos = kwargs.get('pos')
		self.app = kwargs.get('app')
		self.win = self.app.win
		self.api = self.app.api
		self.img = self.app.img
		self.img_dir = self.app.__addon_path__+'/resources/skins/Default/media/'
		self.listcontrol_id = 3150
		self.list_ready = False
		self.tracks_ready = False
		self.thr1 = {}
		self.thr2 = {}
		self.thr3 = {}



	def onInit(self):
		self.view = self.win.handle.getProperty('browseview')
		self.list_instance = self.app.get_var('view_matrix')[self.view]
		self.clist = self.getControl(self.listcontrol_id)
		self.app.set_var('alb_dialog_id', self.id)
		#print self.app.get_var('alb_dialog_id')
		self.show_info(self.id, self.cache)


	def show_info(self, alb_id, cache):

		def get_art(self, cache, album):
			static_id = self.id[:]
			#print "Get art for "+static_id
			self.manage_artwork(cache, album)
			if static_id == self.id:
				#self.manage_windowtracklist(cache, album)
				self.getControl(7).setImage(album["bigthumb"])
				#self.manage_windowtracklist(cache, album)
			else:
				pass
				#print "********* got image but not showing it right now ******"

		def get_review(self, cache, album):
			static_id = self.id[:]
			#print "Get review for "+self.id
			self.manage_review(cache, album)
			if static_id == self.id:
				#print self.id
				self.getControl(14).setText(album["review"])
			else:
				pass
				#print "********* got review but not showing it right now ******"

		def get_details(self, cache, album):
			static_id = self.id[:]
			#print "Get details for "+self.id
			self.manage_details(cache, album)			
			if static_id == self.id:
				self.manage_windowtracklist(cache, album)
				self.getControl(10).setLabel(album["style"])
				#self.getControl(10).setLabel(album["label"])
				self.getControl(6).setLabel(album["tags"]+album['type'])
			else:
				pass
				#print "********* got details but not showing it right now ******"


		#print "AlbumDialog: album id = "+self.id
		self.list_ready = False
		album = cache[alb_id]
		self.reset_fields()
		#self.clearList()
		self.clist.reset()
		self.getControl(11).setText(album["album"])
		self.getControl(13).setLabel(album["artist"])
		self.getControl(8).setLabel(album["album_date"])
		thread.start_new_thread(get_art, (self, cache, album))
		thread.start_new_thread(get_review, (self, cache, album))
		thread.start_new_thread(get_details, (self, cache, album))
		# thread.start_new_thread(self.manage_windowtracklist, (cache, album))
		# self.thr1 = threading.Thread(target=get_art(self, cache, album))
		# self.thr2 = threading.Thread(target=get_review(self, cache, album))
		# self.thr3 = threading.Thread(target=get_details(self, cache, album))
		# self.thr1.start()
		# self.thr2.start()
		# self.thr3.start()
		


		


	def show_next_album(self, offset):
		self.pos = (self.pos+offset) % len(self.current_list)
		self.id = self.current_list[self.pos]#['album_id']
		self.app.set_var('alb_dialog_id', self.id)
		self.show_info(self.id, self.cache)
		#print str(self.pos)
		#print len(self.current_list)

	def manage_windowtracklist(self, cache, album):
		#print "AlbumDialog: Manage tracklist for gui list"

		self.list_ready = False
		while self.tracks_ready == False:
			xbmc.sleep(100)
			print "waiting for tracks..."
		liz = self.app.windowtracklist.get_album_litems(cache, album["album_id"])
		for item in liz:
			self.clist.addItem(item)
		self.win.sync_playlist_pos()
		self.list_ready = True
		print "self.clist.size: "+str(self.clist.size())

	def onAction(self, action):
		#print action
		#print str(action.getId())
		if action.getId() == 1:                     # --- left arrow ---
			if self.getFocusId() == 31:
				self.show_next_album(-1)
		elif action.getId() == 2:                   # --- right arrow ---
			if self.getFocusId() == 31:
				self.show_next_album(1)
		elif action.getId() == 7:                   # --- Enter / Select ---
			if self.getFocusId() == 21:             # --- Play Button ---
				self.start_playback(self.getFocusId(), self.cache[self.id])
			elif self.getFocusId() == 27:           # --- Next Button ---
				self.show_next_album(1)
			elif self.getFocusId() == 26:           # --- Prev Button ---
				self.show_next_album(-1)
			elif self.getFocusId() == self.listcontrol_id:           # --- Tracklist ---
				self.start_playback(self.getFocusId(), self.cache[self.id])
			elif self.getFocusId() == 23:			# --- ADD TO QUEUE ---
				pass
			elif self.getFocusId() == 24:			# --- ADD TO PLAYLIST ---
				pass
			elif self.getFocusId() == 25:			# --- ADD TO LIBRARY ---
				r = self.api.add_album_to_library(self.id)
				if r:
					xbmc.executebuiltin("XBMC.Notification(Rhapsody, Added to Library..., 2000, %s)" %(self.app.__addon_icon__))
					#self.app.lib_albums.fresh = False
					self.app.reinit_lists()
				else:
					xbmc.executebuiltin("XBMC.Notification(Rhapsody, Add to Library failed..., 2000, %s)" %(self.app.__addon_icon__))					
			else: pass
		elif action.getId() == 10:
			self.list_instance.pos = self.pos        # --- Esc ---
			self.close()
		elif action.getId() == 92:                  # --- Back ---
			self.list_instance.pos = self.pos
			self.close()
		elif action.getId() == 18:                  # --- Tab ---
			self.list_instance.pos = self.pos
			self.close()
		else:
			pass


	def start_playback(self, id, album):
		print "Album dialog: start playback"
		if not self.now_playing_matches_album_dialog():
			self.app.player.now_playing = {'pos': 0, 'type':'album', 'item':album['tracks'], 'id':album['album_id']}
			self.app.player.build()
		if self.app.player.now_playing['type'] != 'album':
			self.app.player.now_playing = {'pos': 0, 'type':'album', 'item':album['tracks'], 'id':album['album_id']}
			self.app.player.build()
		if id == self.listcontrol_id:
			self.app.player.now_playing['pos'] = self.clist.getSelectedPosition()
		#xbmc.executebuiltin("XBMC.Notification(Rhapsody, Fetching song..., 5000, %s)" %(self.app.__addon_icon__))
		#self.app.player.get_session()
		thread.start_new_thread(self.app.player.get_session, () )
		self.app.player.check_session = False
		if id == 21:
			print "id is 21, let's select the playing track and focus the tracklist"
			while not self.tracks_ready:
				if self.list_ready:
					return
				xbmc.sleep(100)
				print str(self.list_ready)+": waiting for list"
			self.app.player.now_playing = {'pos': 0, 'type':'album', 'item':album['tracks'], 'id':album['album_id']}
			self.app.player.build()
			self.app.player.playselected(self.app.player.now_playing['pos'])
			#xbmc.executebuiltin("XBMC.Notification(Rhapsody, Playback started, 2000, %s)" %(self.app.__addon_icon__))
			self.clist.selectItem(self.app.playlist.getposition())
			self.setFocusId(self.listcontrol_id)
		else:
			self.app.player.playselected(self.app.player.now_playing['pos'])
			#xbmc.executebuiltin("XBMC.Notification(Rhapsody, Playback started, 2000, %s)" %(self.app.__addon_icon__))
		#thread.start_new_thread(self.app.player.session_test, () )
		#remove this when session handling is complete

	def now_playing_matches_album_dialog(self):
		try:
			if self.app.player.now_playing['id'] == self.id:
				return True
			else:
				return False
		except:
			return True


	def reset_fields(self):
		self.getControl(6).setLabel("")
		self.getControl(7).setImage("")
		self.getControl(8).setLabel("")
		self.getControl(10).setLabel("")
		self.getControl(11).setText("")
		self.getControl(13).setLabel("")
		self.getControl(14).setText("")


	def manage_review(self, cache, album):
		alb_id = album["album_id"]
		if album["review"] == "":
			#print "Getting review from Rhapsody"
			review = self.api.get_album_review(alb_id)
			if not review:
				if album['artist_id'] == "Art.0":
					print "No review for Various Artists"
					return
				else:
					review = self.api.get_bio(album['artist_id'])
					print "No review. Trying artist bio for album review space"
				#print review
			if review:
				#print review
				album["review"] = review
			else:
				print "No bio available for this artist either. :-("
				album["review"] = ""
		else:
			#print "Already have the review in memory for this album"
			pass

	def manage_details(self, cache, album):
		self.tracks_ready = False
		alb_id = album["album_id"]
		if album["tracks"] == "":
			# try to get info from cached album data
			if cache.has_key(alb_id) and (cache[alb_id]['tracks'] != ""):
				#print "Using genre, track, and label from cached album data"
				self.tracks_ready = True
			else:
				#print "Getting genre, tracks and label from Rhapsody"
				results = self.api.get_album_details(alb_id)
				if results:
					#album["label"] = results["label"]
					album["label"] = "Unknown Label"
					album["tracks"] = results["tracks"]
					album["genre_id"] = results["tracks"][0]["genre"]["id"]
					#album["style"] = results["primaryStyle"]
					if not (album["genre_id"] in self.app.cache.genre_dict__):
						results = self.api.get_genre_detail(album["genre_id"])
						self.app.cache.genre_dict__[album["genre_id"]] = results["name"]
						self.app.cache.genre_modified = True
						print "** Added missing genre "+album["genre_id"]+" to genre cache ** "+results["name"]
					album["style"] = self.app.cache.genre['genredict'][album['genre_id']]
					self.tracks_ready = True
				else:
					print "Album Detail api not returning response"
					self.tracks_ready = True

		else:
			#print "Using genre, track, and label from cached album data"
			self.tracks_ready = True
			pass

	def manage_artwork(self, cache, album):
		alb_id = album["album_id"]
		if os.path.isfile(cache[alb_id]['bigthumb']):
			return
		else:
			if not album['thumb_url']:
				full_filename = self.img.handler(album['thumb_url'], 'large', 'album')
			else:
				url = self.img.identify_largest_image(alb_id, "album")
				bigthumb = self.img.handler(url, 'large', 'album')
				full_filename = os.path.join(self.img.base_path, bigthumb)
			album["bigthumb"] = full_filename

