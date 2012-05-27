from PyQt4.QtCore import QThread, SIGNAL
import sleekxmpp
from sleekxmpp.xmlstream import ET
import threading
import re

from constants import SHOW, DEFAULT_GROUP


class Client(QThread): 
	def __init__(self, jid, resource, password, show, status):
		QThread.__init__(self)
		self.jabberID = jid
		self.show = show
		self.status = status
		
		# for subscription management
		self.subscribe = []
		self.subscribed = []
		
		if resource != "":
			self.xmpp = sleekxmpp.ClientXMPP(self.jabberID + "/" + resource, password) 
		else:
			self.xmpp = sleekxmpp.ClientXMPP(self.jabberID, password)
		
		self.xmpp.auto_authorize = None
		self.xmpp.auto_subscribe = None
		
		self.xmpp.register_plugin('xep_0030') # Service Discovery
		self.xmpp.register_plugin('xep_0045') # Multi-User Chat
		self.xmpp.register_plugin('xep_0199') # XMPP Ping
		self.xmpp.register_plugin('old_0004') # used by xep_0045 in order to have data forms
		self.xmpp.register_plugin('xep_0249') # groupchat_direct_invite
		self.xmpp.register_plugin('xep_0030') # disco
		
		self.xmpp.add_event_handler("failed_auth", self.handleFailedAuth) 
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
		self.xmpp.add_event_handler('presence_unsubscribed', self.unsubscribedReq)
		self.xmpp.add_event_handler("changed_subscription", self.handleXMPPPresenceSubscription)
		
		self.received = set()
		self.presences_received = threading.Event()

	def handleXMPPPresenceSubscription(self, subscription):
		print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!subscription", subscription["type"]
		print "entering ", self.subscribe, self.subscribed
		userJID = subscription["from"].jid
		if subscription["type"] == "subscribe":
			if userJID in self.subscribed and userJID not in self.subscribe:
				# i add
				self.subscribe.append(userJID)
				# ask if we want
				self.emit(SIGNAL("subscribeReq"), userJID)
			
			elif userJID not in self.subscribed and userJID not in self.subscribe:
				# he adds, starting
				self.subscribe.append(userJID)
				# ask if we want
				self.emit(SIGNAL("subscribeReq"), userJID)
			
		elif subscription["type"] == "subscribed":
			if userJID not in self.subscribed and userJID not in self.subscribe:
				# i add
				self.subscribed.append(userJID)
				self.xmpp.send_presence(pto = userJID, ptype = 'subscribed')
				self.emit(SIGNAL("sendPresenceToBuddy"), userJID)
				print "_________+_________SUBSCRIBE BOTH+++++++++", userJID
				
			elif userJID not in self.subscribed and userJID in self.subscribe:	
				# he started, finishing
				self.subscribed.append(userJID)
				print "_________+_________SUBSCRIBE Both+++++++", userJID
				
		print "before ", self.subscribe, self.subscribed
		if userJID in self.subscribe and userJID in self.subscribed:			
			self.subscribe.remove(userJID)
			self.subscribed.remove(userJID)
		print "leaving ", self.subscribe, self.subscribed
				
	def subscribeResp(self, resp, userJID, group = None):
		# approve or reject subscription
		if resp:
			print "enter ", self.subscribe, self.subscribed
			if userJID not in self.subscribed and userJID in self.subscribe:
				# he adds
				self.xmpp.send_presence(pto = userJID, ptype = 'subscribed')
				self.emit(SIGNAL("sendPresenceToBuddy"), userJID)
				self.xmpp.send_presence(pto = userJID, ptype = 'subscribe')
				print "_________+_________SUBSCRIBE FROM++++++++", userJID
			elif userJID not in self.subscribed and userJID not in self.subscribe:
				# i add, starting
				self.xmpp.send_presence(pto = userJID, ptype = 'subscribe')
				
			print "bef ", self.subscribe, self.subscribed
			if userJID in self.subscribe and userJID in self.subscribed:
				self.subscribe.remove(userJID)
				self.subscribed.remove(userJID)
			print "lea ", self.subscribe, self.subscribed
		else:
			self.xmpp.send_presence(pto = userJID, ptype = 'unsubscribed')

	def stop(self):
		self.xmpp.disconnect(wait=True)
		self.emit(SIGNAL("debug"), "disconnected\n\n")

	def run(self) : 
		if self.xmpp.connect():
			self.emit(SIGNAL("debug"), "connected\n\n")
			self.xmpp.process(block=True)
		else:
			self.emit(SIGNAL("debug"), "unable to connect\n\n")

	def handleFailedAuth(self, failure):
		# failed_auth
		self.emit(SIGNAL("failedAuth"))
		self.xmpp.disconnect(wait=True)
		
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
	"""
	def subscribeReq(self, presence):
		# presence_subscribe - new subscription request
		#print "\n+++++++++++presence_subscribe ", presence, "+++++++++++++++++"
		# If the subscription request is rejected.
		self.subscribe.append(presence['from'])
		self.emit(SIGNAL("subscribeReq"), str(presence['from']))
		
	def subscribeResp(self, resp, jid, group = None):
		# approve or reject subscription
		#print "\n+++++++++++++++responce ", group, type(group), jid, type(jid), "++++++++++++++++++"
		if resp:
			#print "entering__________\n", self.subscribe, self.subscribed, "\n___________"
			if jid in self.subscribe and jid not in self.subscribed:
				# responce to request
				#print "responce to request"
				self.xmpp.send_presence(pto = jid, ptype = 'subscribed')
				self.subscribed.append(jid)
				# bidirectional
				self.xmpp.send_presence(pto = jid, ptype = 'subscribe')
				self.emit(SIGNAL("sendPresenceToBuddy"))
			elif jid not in self.subscribe and jid not in self.subscribed:
				# we initiate subscription
				#print "we initiate subscription"
				#print "_________+_________SUBSCRIBE TO", jid
				self.xmpp.send_presence(pto = jid, ptype = 'subscribe')
				
				self.subscribe.append(jid)
				
			if jid in self.subscribe and jid in self.subscribed:
				
				self.subscribe.remove(jid)
				self.subscribed.remove(jid)
				#self.emit(SIGNAL("subscribeReq"), str(jid))
				#print "_________+_________SUBSCRIBE BOTH (if i add), FROM (if smb adds+to show item)", jid
				
			#print "leaving__________\n", self.subscribe, self.subscribed, "\n___________"
		else:
			self.xmpp.send_presence(pto = jid, ptype = 'unsubscribed')

	def subscribed(self, presence):
		# presence_subscribed
		print "\n!!!!!!!!!!!!!presence_subscribed ", presence, "!!!!!!!!!!!!!!!!!!!!"
		# Store the new subscription state, somehow. Here we use a backend object.
		#self.subscribed.append(presence['from'])

		# Send a new presence update to the subscriber.
		#self.xmpp.send_presence(pto = presence['from'])
		#print "entering__________\n", self.subscribe, self.subscribed, "\n___________"
		#if presence['from'] in self.subscribe and presence['from'] in self.subscribed:
		#	self.subscribe.remove(presence['from'])
		#	self.subscribed.remove(presence['from'])
			#print "_________+_________SUBSCRIBE BOTH", presence['from']
		#print "leaving__________\n", self.subscribe, self.subscribed, "\n___________"
		"""		
	def unsubscribe(self, jid):
		# remove subscription from contact
		self.xmpp.send_presence(pto = jid, ptype = 'unsubscribe')
		self.xmpp.update_roster(jid, subscription='remove')
		if jid in self.subscribe: self.subscribe.remove(jid)
		if jid in self.subscribed: self.subscribed.remove(jid)
	
	def unsubscribedReq(self, presence):
		# presence_unsubscribed - approvement of removing subscription
		self.emit(SIGNAL("unsubscribedReq"), str(presence['from']))
		if presence['from'] in self.subscribe: self.subscribe.remove(presence['from'])
		if presence['from'] in self.subscribed: self.subscribed.remove(presence['from'])
	
	def dicsoveryJid(self, jid):
		try:
			return self.xmpp.plugin['xep_0030'].get_info(jid)
		except:
			return False

	def handleGroupchatDirectInvite(self, invite):
		# groupchat_direct_invite
		if invite['body'] != "":
			emailPattern = """([\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4})"""
			jidFrom = re.findall(emailPattern, invite['body'])
		else:
			jidFrom[0] = None
			
		self.emit(SIGNAL("inviteMUC"), str(invite['groupchat_invite']['jid']), jidFrom[0])
		
	def declineMUCInvite(self, room, jid, reason='', mfrom=''):
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
		
	def joinMUC(self, jidList):
		room = self.jidlistToRoom(jidList)
		self.xmpp.plugin['xep_0045'].joinMUC(room,
										self.getJidNick(self.jabberID),
										# If a room password is needed, use:
										# password=the_room_password,
										wait=True)
		
	def createMUC(self, jidList):
		room = self.jidlistToRoom(jidList)
		if not self.dicsoveryJid(room):
			self.xmpp.plugin['xep_0045'].joinMUC(room,
										self.getJidNick(self.jabberID),
										# If a room password is needed, use:
										# password=the_room_password,
										wait=True)
			form = self.xmpp.plugin['xep_0045'].getRoomForm(room)			
			conf = self.xmpp.plugin['xep_0045'].configureRoom(room)
			if conf == False:
				return False
			elif conf == True:
				for jid in jidList:
					if str(jid) != str(self.jabberID):
						self.xmpp.plugin['xep_0045'].invite(room, jid)
				return True
		else:
			self.joinMUC(jidList)
		
	def leaveMUC(self, room):
		self.xmpp.plugin['xep_0045'].leaveMUC(room, self.getJidNick(self.jabberID))

	def handleGroupchatMessage(self, message):
		# groupchat_message
		#print "________________________________________groupchat_message\n", message, "\n________________________________________________"
		if message['mucnick'] != self.getJidNick(self.jabberID):
			self.emit(SIGNAL("debug"), "MUC message from " + message["from"].bare + " " + message['mucnick'] + 
				":\n" + message["body"] + "\n\n")
			self.emit(SIGNAL("messageMUC"), (message["from"].bare, message['mucnick'], message["body"]))

	def handleGroupchatPresence(self, presence):
		# groupchat_presence
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
		#print "________________________________________message\n", message, "\n________________________________________________"
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
		if True:#presence['muc']['nick'] == "":
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
		self.emit(SIGNAL("presenceOnline(PyQt_PyObject)"), (presence['from'].bare, "online"))
		self.emit(SIGNAL("debug"), "user " + presence['from'].bare + " went online\n\n")
	
	def getGroups(self, jid):
		if self.xmpp.client_roster[jid]["groups"]:
			return self.xmpp.client_roster[jid]["groups"]
		else:
			return [DEFAULT_GROUP]
			
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
		
	def changeStatus(self, show = "", status = "", jidTo = None):
		# send a presence packet
		if show == 5: #offline
			self.emit(SIGNAL("disconnect"))
		else:
			if jidTo:
				self.xmpp.send_presence(pshow = SHOW[show], pstatus = status, pto = jidTo)
			else:
				self.xmpp.send_presence(pshow = SHOW[show], pstatus = status)
		self.emit(SIGNAL("debug"), "updated presence sent. show: '" + SHOW[show] + 
			"'; status: '" + status + "'\n\n")
