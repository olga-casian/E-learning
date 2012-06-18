from PyQt4.QtCore import QThread, SIGNAL
import sleekxmpp
from sleekxmpp.xmlstream import ET
from sleekxmpp.xmlstream.handler.callback import Callback
from sleekxmpp.xmlstream.matcher.xpath import MatchXPath
import threading
import re
import hashlib

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
			#self.xmpp = sleekxmpp.ClientXMPP(self.jabberID + "/" + resource, hashlib.sha1(password).hexdigest())#password)
			self.xmpp = sleekxmpp.ClientXMPP(self.jabberID + "/" + resource, password) 
		else:
			self.xmpp = sleekxmpp.ClientXMPP(self.jabberID, hashlib.sha1(password).hexdigest())#password)
		
		# custom subscription handling
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
		self.xmpp.add_event_handler('presence_unsubscribe', self.handleUnsubscribeReq)
		self.xmpp.add_event_handler('presence_unsubscribed', self.handleUnsubscribedReq)
		self.xmpp.add_event_handler("changed_subscription", self.handleChangedSubscription)
		self.xmpp.register_handler(Callback('Whiteboarding', 
			MatchXPath('{%s}message/{%s}x/{%s}path' % (self.xmpp.default_ns, 'http://jabber.org/protocol/swb', 'http://jabber.org/protocol/swb')), 
				self.rcvCanvasStroke))
		
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

	def rcvCanvasStroke(self, data):
		rcvFrom = data["from"].bare		
		strokeData = data.xml.find('{%s}x/{%s}path' % ('http://jabber.org/protocol/swb', 'http://jabber.org/protocol/swb'))
		d = strokeData.attrib['d']
		stroke = strokeData.attrib['stroke']
		stroke_width = strokeData.attrib['stroke-width']
		
		if data["type"] == "groupchat":
			nick = data["nick"]
			self.emit(SIGNAL("rcvCanvasStrokeMUC"), nick, rcvFrom, d, stroke, stroke_width)
		elif data["type"] == "chat":
			self.emit(SIGNAL("rcvCanvasStroke"), rcvFrom, d, stroke, stroke_width)

	def sendCanvasStroke(self, msgType, jid, d, stroke, stroke_width):
		"""
		<message to='timon@shakespeare.lit/hall'>
		  <x xmlns='http://jabber.org/protocol/swb'>
			<path d='300 100 200 300 100 100' stroke='#ff0000' stroke-width='1''/>
		  </x>
		</message>
		"""
		if msgType == "groupchat":
			jid = self.jidlistToRoom(jid)
		nick = self.getJidNick(self.jabberID)
		msg = self.xmpp.makeMessage(mto = jid, mtype = msgType, mnick = nick)
		x = ET.Element('{http://jabber.org/protocol/swb}x')
		msg.append(x)
		path = ET.Element('{http://jabber.org/protocol/swb}path', {'d': d, 'stroke': stroke, 'stroke-width':stroke_width})
		x.append(path)
		self.xmpp.send(msg)

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
		
	def handleChangedSubscription(self, subscription):
		# changed_subscription
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
				self.emit(SIGNAL("presence(PyQt_PyObject)"), (userJID, "", self.getSubscription(userJID)))
				
			elif userJID not in self.subscribed and userJID in self.subscribe:	
				# he started, finishing
				self.subscribed.append(userJID)
				self.emit(SIGNAL("presence(PyQt_PyObject)"), (userJID, "", self.getSubscription(userJID)))
				
		if userJID in self.subscribe and userJID in self.subscribed:			
			self.subscribe.remove(userJID)
			self.subscribed.remove(userJID)
				
	def subscribeResp(self, resp, userJID, group = None):
		# approve or reject subscription
		if resp:
			if userJID not in self.subscribed and userJID in self.subscribe:
				# he adds
				self.xmpp.send_presence(pto = userJID, ptype = 'subscribed')
				self.emit(SIGNAL("sendPresenceToBuddy"), userJID)
				self.xmpp.send_presence(pto = userJID, ptype = 'subscribe')
				self.emit(SIGNAL("presence(PyQt_PyObject)"), (userJID, "", self.getSubscription(userJID)))
			elif userJID not in self.subscribed and userJID not in self.subscribe:
				# i add, starting
				self.xmpp.send_presence(pto = userJID, ptype = 'subscribe')
				
			if userJID in self.subscribe and userJID in self.subscribed:
				self.subscribe.remove(userJID)
				self.subscribed.remove(userJID)
		else:
			self.xmpp.send_presence(pto = userJID, ptype = 'unsubscribed')	
		
	def unsubscribe(self, jid):
		# remove subscription from contact
		self.xmpp.send_presence(pto = jid, ptype = 'unsubscribe')
		self.xmpp.update_roster(jid, subscription='remove')
		if jid in self.subscribe: self.subscribe.remove(jid)
		if jid in self.subscribed: self.subscribed.remove(jid)
	
	def handleUnsubscribedReq(self, presence):
		# presence_unsubscribed - approvement of removing subscription
		self.emit(SIGNAL("handleUnsubscribedReq"), str(presence['from']))
		if presence['from'] in self.subscribe: self.subscribe.remove(presence['from'])
		if presence['from'] in self.subscribed: self.subscribed.remove(presence['from'])
		self.emit(SIGNAL("presence(PyQt_PyObject)"), (presence['from'], "", self.getSubscription(presence['from'])))
		
	def handleUnsubscribeReq(self, presence):
		# presence_unsubscribed - approvement of removing subscription
		self.emit(SIGNAL("information"), "Subscription update", "User " + presence['from'] + 
			" has unsubscribed from receiving your status notifications.")
		if presence['from'] in self.subscribe: self.subscribe.remove(presence['from'])
		if presence['from'] in self.subscribed: self.subscribed.remove(presence['from'])
		self.emit(SIGNAL("presence(PyQt_PyObject)"), (presence['from'], "", self.getSubscription(presence['from'])))
	
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
		"""
		<message to="qwertytest@conference.talkr.im">
		<x xmlns="http://jabber.org/protocol/muc#user">
		<decline to="dae-eklen@talkr.im" />
		</x>
		</message>
		"""
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
			self.emit(SIGNAL("presence(PyQt_PyObject)"), (jid, show, self.getSubscription(jid)))
			self.emit(SIGNAL("debug"), "user " + presence['from'].bare + " has new show: '" + 
				show + "'\n\n")
		
	def handleGotOffline(self, presence):
		# got_offline
		if presence['type'] == "unavailable":
			self.emit(SIGNAL("presence(PyQt_PyObject)"), (presence['from'].bare, "offline", 
				self.getSubscription(presence['from'].bare)))
			self.emit(SIGNAL("debug"), "user " + presence['from'].bare + " went offline\n\n")
	
	def handleGotOnline(self, presence):
		self.emit(SIGNAL("presenceOnline(PyQt_PyObject)"), (presence['from'].bare, "online", 
			self.getSubscription(presence['from'].bare)))
		self.emit(SIGNAL("debug"), "user " + presence['from'].bare + " went online\n\n")
	
	def getGroups(self, jid):
		if self.xmpp.client_roster[jid]["groups"]:
			return self.xmpp.client_roster[jid]["groups"]
		else:
			return [DEFAULT_GROUP]
			
	def getSubscription(self, jid):
		if self.xmpp.client_roster[jid]["subscription"]:
			return self.xmpp.client_roster[jid]["subscription"]
		else:
			return False
			
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
