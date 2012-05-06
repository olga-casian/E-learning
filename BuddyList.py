from PyQt4.QtGui import QTreeWidget, QTreeWidgetItem, QMenu, QIcon
from PyQt4.QtCore import Qt, SIGNAL
import time

from BuddyItem import BuddyItem
from AbstractContactList import AbstractContactList


class BuddyList(AbstractContactList):
	"""BuddyList implements the view in a Tree of the Roster"""

	def __init__(self, parent):
		AbstractContactList.__init__(self, parent)
		
		self.setContextMenuPolicy(Qt.CustomContextMenu)
		self.menu = QMenu()
		self.menu.addAction(QIcon("images/rename.png"), "Rename", self.rename)
		self.menu.addAction(QIcon("images/infos.png"), "User Infos", self.getInfo)
		
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
					self.buddies[jid] = BuddyItem(self.groups[group], jid, show, self.connection)
					self.buddies[jid].setName(self.connection.getName(jid))
				self.groups[group].addChild(self.buddies[jid])
				self.tree[group][jid] = self.buddies[jid]
				
	def sendMessage(self, item, col):
		if item and item.type() == QTreeWidgetItem.UserType + 1:
			item.createMsgDialog()
			
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
		
	def rename(self):
		self.emit(SIGNAL("rename"), self.currentItem)

	def getInfo(self):
		pass
