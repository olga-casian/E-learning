from PyQt4.QtCore import Qt

from AbstractListItem import AbstractListItem


class ChatMembersItem(AbstractListItem):
	def __init__(self, parent, jid, show, con, member):
		AbstractListItem.__init__(self, parent, jid, show, con)
		
		self.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
		self.setState(member)
		self.setToolTip(2, self.name + " <" + self.jid + ">")
		
	def checkIfMember(self):
		# returns: 2 - checked; 0 - unchecked
		return self.checkState(0)	
	
	def setState(self, member):
		self.setCheckState(0, member)
