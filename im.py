from PyQt4.QtCore import QThread, SIGNAL
import sleekxmpp
import threading
import re

from constants import SHOW


class Client(QThread): 
	def __init__(self, jid, password, show, status):
		QThread.__init__(self)
		self.jabberID = jid
		self.show = show
		self.status = status
		
		self.xmpp = sleekxmpp.ClientXMPP(self.jabberID, password) 
		
		self.xmpp.register_plugin('xep_0030') # Service Discovery
		self.xmpp.register_plugin('xep_0045') # Multi-User Chat
		self.xmpp.register_plugin('xep_0199') # XMPP Ping
		self.xmpp.register_plugin('old_0004') # xep_0045 depends on old_0004 in order to have data forms
		
		self.xmpp.add_event_handler("session_start", self.handleXMPPConnected) 
		self.xmpp.add_event_handler("message", self.handleIncomingMessage)
		self.xmpp.add_event_handler("changed_status", self.handleStatusChanged)
		self.xmpp.add_event_handler("got_offline", self.handleGotOffline)
		# The groupchat_message event is triggered whenever a message
		# stanza is received from any chat room. If you also also
		# register a handler for the 'message' event, MUC messages
		# will be processed by both handlers.
		self.xmpp.add_event_handler("groupchat_message", self.handleGroupchatMessage)
		# The groupchat_presence event is triggered whenever a
		# presence stanza is received from any chat room, including
		# any presences you send yourself. To limit event handling
		# to a single room, use the events muc::room@server::presence,
		# muc::room@server::got_online, or muc::room@server::got_offline.
		#self.xmpp.add_event_handler("muc::%s::got_online" % self.room, self.muc_online)
		self.xmpp.add_event_handler("groupchat_presence", self.handleGroupchatPresence)
		
		self.received = set()
		self.presences_received = threading.Event()

	def stop(self):
		self.xmpp.disconnect(wait=True)
		self.emit(SIGNAL("debug"), "disconnected\n\n")

	def run(self) : 
		if self.xmpp.connect():
			self.emit(SIGNAL("debug"), "connected\n\n")
			self.xmpp.process(block=True)
		else:
			self.emit(SIGNAL("debug"), "unable to connect\n\n")

	def handleXMPPConnected(self, event): 
		# session_start
		self.xmpp.sendPresence(pstatus = self.status, pshow = self.show)
		self.emit(SIGNAL("debug"), "initial presence sent. show: '" + self.show + 
			"'; status: '" + self.status + "'\n\n")
		
		try:
			self.xmpp.get_roster()
		except IqError as err:
			self.emit(SIGNAL("debug"), "there was an error getting the roster\n" + 
				err.iq["error"]["condition"] + "\n\n")
			self.disconnect()
		except IqTimeout:
			self.emit(SIGNAL("debug"), "server is taking too long to respond\n\n")
			self.disconnect()	
			
		self.emit(SIGNAL("sessionStarted(PyQt_PyObject)"), self.xmpp.client_roster.keys())

	def joinMUC(self, jidList):
		jidList = jidList.append(self.jabberID)
		accountPattern = """([\w\-][\w\-\.]*)+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}"""
		found = re.findall(accountPattern, str(jidList))
		room = ""
		for el in found:
			room += el + "|"		
		room = room[:-1] + "@conference.talkr.im"
		print "!!!!!!!!!!!!", room
		self.xmpp.plugin['xep_0045'].joinMUC(room,
										self.getName(self.jabberID),
										# If a room password is needed, use:
										# password=the_room_password,
										wait=True)
		print "+++++++joinMUC"
		form = self.xmpp.plugin['xep_0045'].getRoomForm(room)
		print "----------------------\n", form, "\n------------------------\n"
		
		print "+++++++configureRoom"
		conf = self.xmpp.plugin['xep_0045'].configureRoom(room)
		if conf == False:
			print "+++++++++++++++++++++++ room config error +++++++++++++++++++++++"
		elif conf == True:
			print "+++++++++++++++++++++++ new romm successfully configured +++++++++++++++++++++++"
			
		print "+++++++invite"
		for jid in jidList:
			self.xmpp.plugin['xep_0045'].invite(room, jid)		

	def handleGroupchatMessage(self, message):
		# groupchat_message
		print "\n!!!!!!!!!!!!!!!groupchat_message\n", message['type'], message, "\n!!!!!!!!!!!!!!!"

	def handleGroupchatPresence(self, presence):
		# groupchat_presence
		print "\n!!!!!!!!!!!!!!!groupchat_presence\n", presence, "\n!!!!!!!!!!!!!!!"

	def sendMUCMessage(self, jids, message):
		pass

	def handleIncomingMessage(self, message): 
		# message
		if message['type'] in ('normal', 'chat'):
			self.emit(SIGNAL("debug"), "message from " + message["from"].bare + ":\n" + message["body"] + "\n\n")
			self.emit(SIGNAL("message"), (message["from"].bare, message["body"]))
		
	def sendMessage(self, tojid, message):
		self.xmpp.sendMessage(mto = tojid, mbody = message, mtype='chat')
		self.emit(SIGNAL("debug"), "message to " + tojid + ":\n" + message + "\n\n")
	
	def handleStatusChanged(self, presence):
		# changed_status
		jid =  presence['from'].bare
		if presence['show'] == "": show = "available"
		else: show =  presence['show']
		#status =  presence['status']
		self.emit(SIGNAL("presence(PyQt_PyObject)"), (jid, show))
		self.emit(SIGNAL("debug"), "user " + presence['from'].bare + " has new show: '" + 
			show + "'\n\n")
		
	def handleGotOffline(self, presence):
		# got_offline
		if presence['type'] == "unavailable":
			self.emit(SIGNAL("presence(PyQt_PyObject)"), (presence['from'].bare, "offline"))
			self.emit(SIGNAL("debug"), "user " + presence['from'].bare + " went offline\n\n")
	
	def getGroups(self, jid):
		if self.xmpp.client_roster[jid]["groups"]:
			return self.xmpp.client_roster[jid]["groups"]
		else:
			return ["Buddies"]
			
	def getShow(self, jid):
		if self.xmpp.client_roster.presence(jid):
			for resource in self.xmpp.client_roster[jid].resources.values():
				if resource["show"] is not "": 
					#self.emit(SIGNAL("debug"), resource["show"] + " - " + jid + "\n\n") 
					return resource["show"]
				elif self.xmpp.client_roster.presence(jid): 
					#self.emit(SIGNAL("debug"), "available - " + jid + "\n\n") 
					return "available"
		else: 
			#self.emit(SIGNAL("debug"), "offline - " + jid + "\n\n") 
			return "offline"
		
	def getName(self, jid):
		if self.xmpp.client_roster[jid]["name"] is not "":
			return self.xmpp.client_roster[jid]["name"]
		else: return jid
		
	def changeStatus(self, show = "", status = ""):
		# send a presence packet
		self.xmpp.send_presence(pshow=SHOW[show], pstatus=status)
		self.emit(SIGNAL("debug"), "updated presence sent. show: '" + SHOW[show] + 
			"'; status: '" + status + "'\n\n")
