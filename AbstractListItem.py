from PyQt4.QtGui import QTreeWidgetItem
from PyQt4.QtCore import Qt


class AbstractListItem(QTreeWidgetItem):
	def __init__(self, parent, jid, show, con, nick = None):
		QTreeWidgetItem.__init__(self, parent, jid, QTreeWidgetItem.UserType + 1)

		# QTreeWidgetItem configuration
		#self.setFlags(Qt.ItemIsDragEnabled | Qt.ItemIsEnabled) # we can move a contact
		self.parent = parent
		self.jid = jid
		self.name = jid
		self.connection = con
		self.nick = nick
		
	def setName(self, name):
		if name:
			self.name = name
			self.setText(0, name)
		
	def status(self):
		return status
		
	def __str__(self):
		return self.name
