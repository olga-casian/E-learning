from PyQt4.QtGui import QTreeWidget
from PyQt4.QtCore import Qt

from BuddyGroup import BuddyGroup


class AbstractContactList(QTreeWidget):
	def __init__(self, parent):
		QTreeWidget.__init__(self, parent)
		
		self.connection = None
		self.header().hide()
		self.setSortingEnabled(True)
		self.sortItems(0, Qt.AscendingOrder)
		self.buddies = {}
		self.muc = {}
		self.groups = {}
		self.tree = {}
		
	def setRoster(self, rosterKeys):
		self.rosterKeys = rosterKeys
			
	def setConnection(self, con):
		self.connection = con
		
	def addGroup(self, group):
		if group:
			if group not in self.groups.keys():
				self.groups[group] = BuddyGroup(group)
				self.tree[group] = {}
				self.addTopLevelItem(self.groups[group])
	
	def presence(self, data):
		jid, show = data
		if str(jid) is not self.connection.jabberID:
			try:
				self.buddies[str(jid)].setStatus(show)
				self.hideGroups()
			except: 
				pass
