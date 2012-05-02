from PyQt4.QtGui import QTreeWidgetItem, QIcon, QDialog, QVBoxLayout, QApplication, QMenu
from PyQt4.QtCore import Qt, QSettings

from MessageDialog import MessageDialog
from constants import SHOW


class BuddyItem(QTreeWidgetItem):
	"""
	  BuddyItem implements the view of a Buddy from the Roster
	"""

	dialog = None
	msg = None

	def __init__(self, parent, jid, show, con):
		QTreeWidgetItem.__init__(self, parent, [jid], QTreeWidgetItem.UserType+1)

		# QTreeWidgetItem configuration
		self.setFlags(Qt.ItemIsDragEnabled | Qt.ItemIsEnabled) # we can move a contact
		self.parent = parent
		self.jid = jid
		self.name = jid
		self.setStatus(show)
		self.connection = con
	
	def setStatus(self, show):
		self.show = show
		fileShow = "interface/resource/icons/status/" + str(self.show) + ".png"
		self.setIcon(0, QIcon(fileShow))

	def setName(self, name):
		if name:
			self.name = name
			self.setText(0, name)

	def status(self):
		return status

	def isAway(self):
		return (self.show == "away" or self.status == "xa")

	def isOffline(self):
		return self.show == "offline"

	def createMsgDialog(self):
		try:
			self.messageDialog.show()
			self.messageDialog.raise_()
		except:
			self.messageDialog = MessageDialog(self.connection, self.jid, self.name)
			self.messageDialog.show()
			self.messageDialog.raise_()

	def receiveMessage(self, buddy, msg):
		self.createMsgDialog()
		self.messageDialog.receiveMessage(msg)

	def __str__(self):
		return u'%s' % self.name
