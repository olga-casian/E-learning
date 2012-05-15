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
		self.xmpp.register_plugin('xep_0249') # groupchat_direct_invite
		
		self.xmpp.add_event_handler("session_start", self.handleXMPPConnected) 
		self.xmpp.add_event_handler("message", self.handleIncomingMessage)
		self.xmpp.add_event_handler("changed_status", self.handleStatusChanged)
		self.xmpp.add_event_handler("got_offline", self.handleGotOffline)
		self.xmpp.add_event_handler("got_online", self.handleGotOnline)
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
		self.xmpp.add_event_handler("groupchat_direct_invite", self.handleGroupchatDirectInvite)
		
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

	def handleGroupchatDirectInvite(self, invite):
		# groupchat_direct_invite
		print "\n!!!!!!!!!!!!!!!groupchat_direct_invite\n", invite, "\n!!!!!!!!!!!!!!!"
		print "Received direct muc invitation from %s to room %s", invite['from'], invite['groupchat_invite']['jid']
		print invite['body']
		text = "Received invitation from " + str(invite['from']) + " to room " + str(invite['groupchat_invite']['jid'])
		if invite['body'] != "":
			text += ":\n\n" + invite['body']
		text += "\n\nDo you want to accept the invitation?"
		self.emit(SIGNAL("question"), "Groupchat invitation", text)
		
		"""
		from sleekxmpp.xmlstream import ET
		def decline_invite(self, room, jid, reason='', mfrom=''):
			msg = self.xmpp.makeMessage(room)
			msg['from'] = mfrom
			x = ET.Element('{http://jabber.org/protocol/muc#user}x')
			decline = ET.Element('{http://jabber.org/protocol/muc#user}decline', {'to': jid})
			if reason:
				rxml = ET.Element('reason')
				rxml.text = reason
				decline.append(rxml)
			x.append(decline)
			msg.append(x)
			self.xmpp.send(msg)
        """
		
	def createMUC(self, jidList):
		room = self.jidlistToRoom(jidList)		
		"""
		self.xmpp.plugin['xep_0045'].joinMUC(room,
										self.getJidNick(self.jabberID),
										# If a room password is needed, use:
										# password=the_room_password,
										wait=True)
		
		print "+++++++joinMUC"
		form = self.xmpp.plugin['xep_0045'].getRoomForm(room) #getRoomConfig
		#print "----------------------\n", form, "\n------------------------\n"
		
		print "+++++++configureRoom"
		conf = self.xmpp.plugin['xep_0045'].configureRoom(room)
		if conf == False:
			print "+++++++++++++++++++++++ room config error +++++++++++++++++++++++"
		elif conf == True:
			print "+++++++++++++++++++++++ new romm successfully configured +++++++++++++++++++++++"
		
		#print "+++++++invite"
		for jid in jidList:
			if jid is not self.jabberID:
				self.xmpp.plugin['xep_0045'].invite(room, jid)	
		"""
		print "!!!CREATE MUC"
		self.xmpp.plugin['xep_0045'].joinMUC(room,
										self.getJidNick(self.jabberID),
										# If a room password is needed, use:
										# password=the_room_password,
										wait=True)
		"""
		print "+++++++joinMUC"
		form = self.xmpp.plugin['xep_0045'].getRoomForm(room)
		#print "----------------------\n", form, "\n------------------------\n"
		
		print "+++++++configureRoom"
		conf = self.xmpp.plugin['xep_0045'].configureRoom(room)
		if conf == False:
			print "+++++++++++++++++++++++ room config error +++++++++++++++++++++++"
		elif conf == True:
			print "+++++++++++++++++++++++ new romm successfully configured +++++++++++++++++++++++"
		"""
		#print "+++++++invite"
		print "!!!SEND INVITES"
		for jid in jidList:
			if str(jid) != str(self.jabberID):
				self.xmpp.plugin['xep_0045'].invite(room, jid)
		
	def leaveMUC(self, room):
		self.xmpp.plugin['xep_0045'].leaveMUC(room, self.getJidNick(self.jabberID))

	def handleGroupchatMessage(self, message):
		# groupchat_message
		if message['mucnick'] != self.getJidNick(self.jabberID):
			self.emit(SIGNAL("debug"), "MUC message from " + message["from"].bare + " " + message['mucnick'] + 
				":\n" + message["body"] + "\n\n")
			self.emit(SIGNAL("messageMUC"), (message["from"].bare, message['mucnick'], message["body"]))

	def handleGroupchatPresence(self, presence):
		# groupchat_presence
		#print "\n!!!!!!!!!!!!!!!groupchat_presence\n", presence, "\n!!!!!!!!!!!!!!!"
		jid =  presence['from'].bare
		
		if presence['muc']['nick'] != self.getJidNick(self.jabberID):
			if presence['type'] == "unavailable":
				self.emit(SIGNAL("messageMUC"), (presence["from"].bare, "", presence['muc']['nick'] + " has left the room"))
				self.emit(SIGNAL("debug"), presence['muc']['nick'] + " has left the room " + presence["from"].bare + "\n\n")
			else:
				self.emit(SIGNAL("messageMUC"), (presence["from"].bare, "", presence['muc']['nick'] + " has joined the room"))
				self.emit(SIGNAL("debug"), presence['muc']['nick'] + " has joined the room " + presence["from"].bare + "\n\n")

	def sendMUCMessage(self, jidList, message):
		room = self.jidlistToRoom(jidList)
		self.xmpp.send_message(mto=room,
							mbody=message,
							mtype='groupchat')
		self.emit(SIGNAL("debug"), "message to " + room + ":\n" + message + "\n\n")

	def jidlistToRoom(self, jidList):
		pattern = """([\w\-][\w\-\.]*)+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}"""
		found = re.findall(pattern, str(jidList))
		room = ""
		for el in found:
			room += el + "|"
		room = room[:-1] + "@conference.talkr.im"
		return room

	def handleIncomingMessage(self, message): 
		# message
		if message['type'] in ('normal', 'chat'):
			if not message.match('message/groupchat_invite'):
				self.emit(SIGNAL("debug"), "message from " + message["from"].bare + ":\n" + message["body"] + "\n\n")
				if "conference" in message["from"].bare:
					patternNickFromMUC = """[\w\-\|][\w\-\.\|]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}/([\w\-\|][\w\-\.\|]*)"""
					nick = re.findall(patternNickFromMUC, str(message["from"]))
					self.emit(SIGNAL("message"), (message["from"].bare, message["body"], nick[0]))
				else:
					self.emit(SIGNAL("message"), (message["from"].bare, message["body"], None))
		
	def sendMessage(self, tojid, message):
		self.xmpp.sendMessage(mto = tojid, mbody = message, mtype='chat')
		self.emit(SIGNAL("debug"), "message to " + tojid + ":\n" + message + "\n\n")
	
	def handleStatusChanged(self, presence):
		# changed_status
		if presence['muc']['nick'] == "":
			jid =  presence['from'].bare
			if presence['show'] == "": show = "available"
			else: show =  presence['show']
			self.emit(SIGNAL("presence(PyQt_PyObject)"), (jid, show))
			self.emit(SIGNAL("debug"), "user " + presence['from'].bare + " has new show: '" + 
				show + "'\n\n")
		
	def handleGotOffline(self, presence):
		# got_offline
		if presence['type'] == "unavailable":
			self.emit(SIGNAL("presence(PyQt_PyObject)"), (presence['from'].bare, "offline"))
			self.emit(SIGNAL("debug"), "user " + presence['from'].bare + " went offline\n\n")
	
	def handleGotOnline(self, presence):
		#print "\n+++++++++++ONLINE\n", presence, "\n++++++++++++++++"
		self.emit(SIGNAL("presenceOnline(PyQt_PyObject)"), (presence['from'].bare, "offline"))
		self.emit(SIGNAL("debug"), "user " + presence['from'].bare + " went offline\n\n")
	
	def getGroups(self, jid):
		if self.xmpp.client_roster[jid]["groups"]:
			return self.xmpp.client_roster[jid]["groups"]
		else:
			return ["Buddies"]
			
	def getBuddyShow(self, jid):
		pass
			
	def getShow(self, jids):
		if self.xmpp.client_roster.presence(jids):
			for resource in self.xmpp.client_roster[jids].resources.values():
				if resource["show"] is not "": 
					#self.emit(SIGNAL("debug"), resource["show"] + " - " + jids + "\n\n") 
					return resource["show"]
				elif self.xmpp.client_roster.presence(jids): 
					#self.emit(SIGNAL("debug"), "available - " + jids + "\n\n") 
					return "available"
		else: 
			#self.emit(SIGNAL("debug"), "offline - " + jids + "\n\n") 
			return "offline"
		
	def getName(self, jid):
		if self.xmpp.client_roster[jid]["name"] is not "":
			return self.xmpp.client_roster[jid]["name"]
		else: return jid
		
	def getJidNick(self, jid):
		jidNickPattern = """([\w\-][\w\-\.]*)+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}"""
		nick = re.findall(jidNickPattern, jid)
		return nick[0]
		
	def changeStatus(self, show = "", status = ""):
		# send a presence packet
		self.xmpp.send_presence(pshow=SHOW[show], pstatus=status)
		self.emit(SIGNAL("debug"), "updated presence sent. show: '" + SHOW[show] + 
			"'; status: '" + status + "'\n\n")
