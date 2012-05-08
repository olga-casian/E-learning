from PyQt4.QtCore import QThread, SIGNAL
import sleekxmpp
import threading

from constants import SHOW


class Client(QThread): 
	def __init__(self, jid, password, show, status):
		QThread.__init__(self)
		self.jabberID = jid
		self.show = show
		self.status = status
		
		self.xmpp = sleekxmpp.ClientXMPP(self.jabberID, password) 
		
		self.xmpp.add_event_handler("session_start", self.handleXMPPConnected) 
		self.xmpp.add_event_handler("message", self.handleIncomingMessage)
		self.xmpp.add_event_handler("changed_status", self.handleStatusChanged)
		self.xmpp.add_event_handler("got_offline", self.handleGotOffline)
		
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

	def handleIncomingMessage(self, message): 
		# message
		if message['type'] in ('normal', 'chat'):
			self.emit(SIGNAL("debug"), "message from " + message["from"].bare + ":\n" + message["body"] + "\n\n")
			self.emit(SIGNAL("message"), (message["from"].bare, message["body"]))
		
	def send_message(self, tojid, message):
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
