from PyQt4.QtGui import QTreeWidgetItem, QIcon, QDialog, QVBoxLayout, QApplication, QMenu
from PyQt4.QtCore import Qt, QSettings

from MessageDialog import MessageDialog
from AbstractListItem import AbstractListItem
from constants import SHOW


class BuddyItem(AbstractListItem):
	"""
	  BuddyItem implements the view of a Buddy from the Roster
	"""

	dialog = None
	msg = None

	def __init__(self, buddyList, parent, jid, show, con):
		AbstractListItem.__init__(self, parent, jid, show, con)
		
		self.buddyList = buddyList
		self.setStatus(show)
		
	def setStatus(self, show):
		self.show = show
		fileShow = "interface/resource/icons/status/" + str(self.show) + ".png"
		self.setIcon(0, QIcon(fileShow))

	def createMsgDialog(self):
		try:
			self.messageDialog.show()
			self.messageDialog.raise_()
		except:
			self.messageDialog = MessageDialog(self.connection, self.jid, self.buddyList)
			self.messageDialog.show()
			self.messageDialog.raise_()

	def receiveMessage(self, buddy, msg):
		self.createMsgDialog()
		self.messageDialog.receiveMessage(msg)
		
	def isAway(self):
		return (self.show == "away" or self.status == "xa")
	
	def isOffline(self):
		return self.show == "offline"
