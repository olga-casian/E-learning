from PyQt4.QtCore import QSettings, QSize

from ChatMembersItem import ChatMembersItem
from AbstractContactList import AbstractContactList


class ChatMembers(AbstractContactList):
	def __init__(self, parent):
		AbstractContactList.__init__(self, parent)
		
		self.hide()
		self.setMaximumWidth(250)
		
		self.parent = parent
		self.members = True
	
	def constructList(self):
		self.settings = QSettings("Dae-ekleN", "PyTalk")
		self.settings.beginGroup(self.settings.value(self.connection.jabberID))
		self.rosterKeys = self.settings.value("roster", "")
		self.settings.endGroup()
		
		for jid in self.rosterKeys:
			if self.connection:
				group = self.connection.getGroups(jid)[0]
				self.addGroup(group)
				if jid not in self.buddies.keys():
					show = self.connection.getShow(jid)
					self.buddies[jid] = ChatMembersItem(self.groups[group], jid, show, self.connection)
					self.buddies[jid].setName(self.connection.getName(jid))
				self.groups[group].addChild(self.buddies[jid])
				self.tree[group][jid] = self.buddies[jid]
		#self.expandAll()

	def showMembersBuddies(self, hide):
		self.members = hide
		self.hideGroups()
		
	def hideGroups(self):
		for child in self.buddies.values():
			if child.jid not in self.parent.jidTo:
				child.setHidden(self.members)
			else:
				child.setHidden(False)

		for group in self.tree.keys():
			hide = True
			for child in self.tree[group].values():
				if not child.isHidden():
					hide = False
			self.groups[group].setHidden(hide)
		self.expandAll()
