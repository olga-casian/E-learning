from PyQt4.QtGui import QIcon, QTreeWidgetItem

from MessageDialog import MessageDialog
from AbstractListItem import AbstractListItem
from constants import SHOW


class BuddyItem(AbstractListItem):
	"""
	  BuddyItem implements the view of a Buddy from the Roster
	"""

	dialog = None
	msg = None

	def __init__(self, buddyList, parent, jid, show, con, nick = None, muc = None):
		AbstractListItem.__init__(self, parent, jid, show, con, nick, muc)
		
		self.buddyList = buddyList
		self.setStatus(show)
		
	def setStatus(self, show = "", subscription = ""):
		if show != "": self.show = show
		fileShow = "interface/resource/icons/status/" + str(self.show) + ".png"
		self.setIcon(0, QIcon(fileShow))
		
		name = self.connection.getName(self.jid)
		if name is not self.jid:
			toolTip = name + " <" + str(self.jid) + ">"
		else: toolTip = "<" + str(self.jid) + ">"
		if subscription != "":
			toolTip += "\nSubscription: " + subscription
		self.setToolTip(0, toolTip)

	def createMsgDialog(self):
		try:
			self.messageDialog.show()
			self.messageDialog.raise_()
		except:
			self.messageDialog = MessageDialog(self.connection, self.jid, self.buddyList, self.nick)
			self.messageDialog.show()
			self.messageDialog.raise_()

	def closeDialog(self):
		try:
			self.messageDialog.close()
		except: pass

	def receiveMessage(self, buddy, msg):
		self.createMsgDialog()
		self.messageDialog.receiveMessage(msg)
		
	def isAway(self):
		return (self.show == "away" or self.status == "xa")
	
	def isOffline(self):
		return self.show == "offline"
