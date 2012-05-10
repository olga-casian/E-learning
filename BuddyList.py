from PyQt4.QtGui import QMenu, QIcon, QTreeWidgetItem
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
		#self.menu.addAction(QIcon("images/rename.png"), "Rename", self.rename)
		#self.menu.addAction(QIcon("images/infos.png"), "User Infos", self.getInfo)
		
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
			match = 0
			emailPattern = """[\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}"""
			for keyStr in self.muc.keys():
				keyList = re.findall(emailPattern, keyStr)
				match = 0
				for key in keyList:
					for jid in self.currentItem.jid:
						if str(jid) == str(key):
							match = match + 1
					if len(self.currentItem.jid) == match ==len(keyList):
						# make elements unicode
						for n in range(len(keyList)): keyList[n] = unicode(keyList[n])
						
						del self.tree[MUC_GROUP_TITLE][str(keyList)]						
						self.groups[MUC_GROUP_TITLE].removeChild(self.muc[str(keyList)])
						#self.emit(SIGNAL("closeMUC"))
						
						if len(self.tree[MUC_GROUP_TITLE].keys()) is 0:							
							self.removeGroup(MUC_GROUP_TITLE)
							del self.tree[MUC_GROUP_TITLE]
							
						del self.muc[str(keyList)]												
						self.updateSettingsMUC()
						self.hideGroups()
				
	def constructMUC(self):
		# get MUC from settings
		self.settings = QSettings("Dae-ekleN", "PyTalk")
		self.settings.beginGroup(self.connection.jabberID)
		mucs = self.settings.value("MUC", "")
		self.settings.endGroup()
		
		if mucs is not None:
			self.addGroup(MUC_GROUP_TITLE)
			
			# muc from settings to list		
			emailPattern = """[\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}"""
			for muc in mucs:
				jidsFromOneMUC = re.findall(emailPattern, muc)

				# make elements unicode
				for n in range(len(jidsFromOneMUC)): jidsFromOneMUC[n] = unicode(jidsFromOneMUC[n])
					
				# add MUC item to list
				self.muc[str(jidsFromOneMUC)] = MUCItem(self, self.groups[MUC_GROUP_TITLE], jidsFromOneMUC, "-", self.connection)
				
				titleMUC = "Group chat (" + str(len(jidsFromOneMUC)) + ")"
				self.muc[str(jidsFromOneMUC)].setName(titleMUC)
				
				self.groups[MUC_GROUP_TITLE].addChild(self.muc[str(jidsFromOneMUC)])
				self.tree[MUC_GROUP_TITLE][str(jidsFromOneMUC)] = self.muc[str(jidsFromOneMUC)]
				
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
			for n in range(len(jid)): jid[n] = unicode(jid[n])
			
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
		buddy, msg = data
		if buddy not in self.buddies.keys():
			self.buddies[buddy] = BuddyItem(None, buddy)
		self.buddies[buddy].receiveMessage(buddy, msg)

	def context(self, pos):
		item = self.itemAt(pos)
		if item:
			if item.type() == QTreeWidgetItem.UserType+1:
				self.currentItem = item
				self.menu.popup(self.mapToGlobal(pos))
	"""	
	def rename(self):
		self.emit(SIGNAL("rename"), self.currentItem)

	def getInfo(self):
		pass
	"""
