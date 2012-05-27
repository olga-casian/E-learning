from PyQt4.QtGui import QMenu, QIcon, QTreeWidgetItem, QMessageBox
from PyQt4.QtCore import Qt, SIGNAL, QSettings
import time, re

from constants import MUC_GROUP_TITLE
from BuddyItem import BuddyItem
from AbstractContactList import AbstractContactList
from MUCItem import MUCItem


class BuddyList(AbstractContactList):
	"""BuddyList implements the view in a Tree of the Roster"""

	def __init__(self, parent):
		AbstractContactList.__init__(self, parent)
		
		self.setContextMenuPolicy(Qt.CustomContextMenu)
		self.menu = QMenu()
		self.menu.addAction(QIcon("images/rename.png"), "Remove", self.remove)
				
		self.connect(self, SIGNAL("customContextMenuRequested(QPoint)"), self.context)
		self.connect(self, SIGNAL("itemDoubleClicked(QTreeWidgetItem *,int)"), self.sendMessage)
		
		self.away = False
		self.offline = True
	
	def constructList(self, rosterKeys):
		# wait till all presences will come
		time.sleep(3)
		
		for jid in rosterKeys:
			if self.connection:
				group = self.connection.getGroups(jid)[0]
				self.addGroup(group)
				if jid not in self.buddies.keys():
					show = self.connection.getShow(jid)
					self.buddies[jid] = BuddyItem(self, self.groups[group], jid, show, self.connection)
					self.buddies[jid].setName(self.connection.getName(jid))
				self.groups[group].addChild(self.buddies[jid])
				self.tree[group][jid] = self.buddies[jid]
		self.constructMUC()
		
	def remove(self):
		if type(self.currentItem) is MUCItem:
			print self.currentItem.jid
			reply = QMessageBox.question(self, "Remove Group Chat", "Are you sure to leave group chat " + 
					self.connection.jidlistToRoom(self.currentItem.jid) + 
					"? All private messages through this chat will be closed as well.", 
					QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
			if reply == QMessageBox.Yes:
				self.removeMUC()
				
		elif type(self.currentItem) is BuddyItem:
			reply = QMessageBox.question(self, "Remove Buddy", "Are you sure to remove " + self.currentItem.jid + 
					" from your contact list and unsubscribe?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
			if reply == QMessageBox.Yes:			
				self.removeBuddy(self.currentItem.jid)

	def removeBuddy(self, jid):
		# close windows
		self.buddies[jid].closeDialog()
		
		# remove from tree
		for groupDict in self.tree.values():
			for jidItem in groupDict.keys():
				if jidItem == jid:
					del groupDict[jidItem]
			
		# remove from group
		for group in self.groups:
			for nr in range(self.groups[group].childCount()):
				if str(self.groups[group].child(nr)) == str(jid):
					self.groups[group].removeChild(self.groups[group].child(nr))
						
		# remove from buddies	
		del self.buddies[jid]
		
		self.hideGroups()
		self.connection.unsubscribe(str(jid))

	def removeMUC(self):
		match = 0
		room = ""
		emailPattern = """[\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}"""
		for keyStr in self.muc.keys():
			keyList = re.findall(emailPattern, keyStr)
			match = 0
			for key in keyList:
				for jid in self.currentItem.jid:
					if str(jid) == str(key):
						match = match + 1
						jidPattern = """([\w\-][\w\-\.]*)+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}"""
						nick = re.findall(jidPattern, str(jid))
						room += nick[0] + "|"
				if len(self.currentItem.jid) == match ==len(keyList):
					# clear vars in code:
					for n in range(len(keyList)): keyList[n] = unicode(keyList[n])
					
					# close windows
					self.muc[str(keyList)].closeDialog()
					roomToLeave = self.connection.jidlistToRoom(keyList)
					toDel = []
					for buddy in self.buddies:
						if self.buddies[buddy].muc == roomToLeave: # ex: dae-eklen-test2|dae-eklen-test|dae-eklen@conference.talkr.im
							self.buddies[buddy].closeDialog()
							toDel.append(buddy)
					for el in toDel:
						del self.buddies[el]
								
					del self.tree[MUC_GROUP_TITLE][str(keyList)]						
					self.groups[MUC_GROUP_TITLE].removeChild(self.muc[str(keyList)])
						
					if len(self.tree[MUC_GROUP_TITLE].keys()) is 0:							
						self.removeGroup(MUC_GROUP_TITLE)
						del self.tree[MUC_GROUP_TITLE]
							
					del self.muc[str(keyList)]												
					self.updateSettingsMUC()
					self.hideGroups()
					
					# send unavailable presence:
					room = room[:-1] + "@conference.talkr.im"
					self.connection.leaveMUC(room)
	
	def newBuddy(self, jid, group, show = None):
		self.addGroup(group)
		if jid not in self.buddies.keys():
			if not show:
				show = self.connection.getShow(jid)
			self.buddies[jid] = BuddyItem(self, self.groups[group], jid, show, self.connection)
			self.buddies[jid].setName(self.connection.getName(jid))
		self.groups[group].addChild(self.buddies[jid])
		self.tree[group][jid] = self.buddies[jid]
		self.hideGroups()
				
	def constructMUC(self):
		# get MUC from settings
		self.settings = QSettings("Dae-ekleN", "PyTalk")
		self.settings.beginGroup(self.connection.jabberID)
		mucs = self.settings.value("MUC", "")
		self.settings.endGroup()
		
		if mucs == "":
			return
		if mucs is None:
			return
			
		self.addGroup(MUC_GROUP_TITLE)
			
		# muc from settings to list		
		emailPattern = """[\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}"""
		for mucChat in mucs:
			jidsFromOneMUC = re.findall(emailPattern, mucChat)
			
			# add MUC item to list
			self.muc[str(jidsFromOneMUC)] = MUCItem(self, self.groups[MUC_GROUP_TITLE], jidsFromOneMUC, "-", self.connection)
				
			titleMUC = "Group chat (" + str(len(jidsFromOneMUC)) + ")"
			self.muc[str(jidsFromOneMUC)].setName(titleMUC)
			
			self.groups[MUC_GROUP_TITLE].addChild(self.muc[str(jidsFromOneMUC)])
			self.tree[MUC_GROUP_TITLE][str(jidsFromOneMUC)] = self.muc[str(jidsFromOneMUC)]
				
			# join room
			self.connection.createMUC(jidsFromOneMUC)
				
	def sendMessage(self, item, col):
		if item and item.type() == QTreeWidgetItem.UserType + 1:
			item.createMsgDialog()
			
	def newDialog(self, jid):
		for child in self.buddies.values():
			if child.jid == jid:
				child.createMsgDialog()

	def newMUCItem(self, jid):
		if not self.MUCExists(jid):
			self.addGroup(MUC_GROUP_TITLE)
			# make elements unicode
			for n in range(len(jid)):
				jid[n] = unicode(jid[n])
			
			self.muc[str(jid)] = MUCItem(self, self.groups[MUC_GROUP_TITLE], jid, "-", self.connection)
			
			titleMUC = "Group chat (" + str(len(jid)) + ")"
			self.muc[str(jid)].setName(titleMUC)
			
			self.groups[MUC_GROUP_TITLE].addChild(self.muc[str(jid)])
			self.tree[MUC_GROUP_TITLE][str(jid)] = self.muc[str(jid)]
			
			self.updateSettingsMUC()
			
	def updateSettingsMUC(self):
		self.settings = QSettings("Dae-ekleN", "PyTalk")
		self.settings.beginGroup(self.connection.jabberID)
		self.settings.setValue("MUC", self.muc.keys())
		self.settings.endGroup()
			
	def MUCExists(self, jidList):
		# True - muc exists, False - doesn't
		match = 0
		emailPattern = """[\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}"""
		for keyStr in self.muc.keys():
			keyList = re.findall(emailPattern, keyStr)
			match = 0
			for key in keyList:
				for jid in jidList:
					if str(jid) == str(key):
						match = match + 1
				if len(jidList) == match ==len(keyList):
					return True
		return False

	def newMUCDialog(self, jidTo):
		for child in self.muc.values():
			if child.jid == jidTo:
				child.createMsgDialog()
			
	def showOfflineBuddies(self, hide):
		self.offline = hide
		self.hideGroups()  

	def showAwayBuddies(self, hide):
		self.away = hide
		self.hideGroups()
		
	def hideGroups(self):
		for child in self.buddies.values():
			if child.isOffline():
				child.setHidden(self.offline)
			elif child.isAway():
				child.setHidden(self.away)
			else:
				child.setHidden(False)

		for group in self.tree.keys():
			hide = True
			for child in self.tree[group].values():
				if not child.isHidden():
					hide = False
			self.groups[group].setHidden(hide)
		self.expandAll()

	def message(self, data):
		buddy, msg, nick = data
		if nick:
			# private msg from muc member
			if buddy + "/" + nick not in self.buddies.keys():
				self.buddies[buddy + "/" + nick] = BuddyItem(None, self.groups[MUC_GROUP_TITLE], buddy + "/" + nick, "-", 
					self.connection, nick, buddy)
				self.buddies[buddy + "/" + nick].setName(nick + " from " + buddy)
				self.buddies[buddy + "/" + nick].receiveMessage(buddy + "/" + nick, msg)
		else:
			# usual private msg
			"""
			# currently receives only from items in roster
			if buddy not in self.buddies.keys():
				self.buddies[buddy] = BuddyItem(None, self.groups[MUC_GROUP_TITLE], buddy, "-", self.connection)
				self.buddies[buddy].setName(self.connection.getName(buddy))
			"""
			self.buddies[buddy].receiveMessage(buddy, msg)
		
	def messageMUC(self, data):
		muc, nick, msg = data
		# get group name
		pattern = """([\w\-\|][\w\-\.\|]*)+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}"""
		jidsFromOneMUC = re.findall(pattern, str(muc))
		
		# set list of members
		jidsFromOneMUC = jidsFromOneMUC[0].split("|")
		
		# add server
		for n in range(len(jidsFromOneMUC)): jidsFromOneMUC[n] = unicode(jidsFromOneMUC[n] + "@talkr.im")

		self.newMUCItem(jidsFromOneMUC)
		self.muc[str(jidsFromOneMUC)].receiveMessage(nick, msg)

	def context(self, pos):
		item = self.itemAt(pos)
		if item:
			if item.type() == QTreeWidgetItem.UserType+1:
				self.currentItem = item
				self.menu.popup(self.mapToGlobal(pos))
				
	def clear(self):
		for buddy in self.buddies:
			try:
				self.buddies[buddy].closeDialog()
				self.buddies[buddy].messageDialog = None
			except: pass
		self.buddies = {}
		
		for el in self.tree:
			self.removeGroup(el)
		self.tree = {}
		
		for el in self.groups.values():
			el.takeChildren()
		self.groups = {}
		
		for el in self.muc.values():
			try:
				el.closeDialog()
				el.MUCDialog = None
			except: pass
		self.muc = {}
		
		self.connection = None
