from PyQt4.QtGui import QIcon, QTreeWidgetItem

from MUCDialog import MUCDialog
from AbstractListItem import AbstractListItem
from constants import SHOW


class MUCItem(AbstractListItem):
	dialog = None
	msg = None

	def __init__(self, buddyList, parent, jid, show, con):
		AbstractListItem.__init__(self, parent, jid, show, con)
		
		self.buddyList = buddyList
		
		toolTip = ""
		for jid in self.jid:
			name = self.connection.getName(jid)
			if name is not jid:
				toolTip += name + " <" + str(jid) + ">, \n"
			else: toolTip += "<" + str(jid) + ">, \n"
		self.setToolTip(0, toolTip[:-3])
		
	def createMsgDialog(self):
		try:
			self.MUCDialog.show()
			self.MUCDialog.raise_()
		except:
			self.MUCDialog = MUCDialog(self.connection, self.jid, self.buddyList)
			self.MUCDialog.show()
			self.MUCDialog.raise_()
			
	def closeDialog(self):
		self.MUCDialog.close()
			
	def receiveMessage(self, nick, msg):
		self.createMsgDialog()
		self.MUCDialog.receiveMessage(nick, msg)

