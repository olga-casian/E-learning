from PyQt4.QtGui import QTreeWidgetItem, QIcon, QDialog, QVBoxLayout, QApplication, QMenu
from PyQt4.QtCore import Qt, QSettings


class AbstractListItem(QTreeWidgetItem):
	def __init__(self, parent, jid, show, con):
		QTreeWidgetItem.__init__(self, parent, [jid], QTreeWidgetItem.UserType+1)

		# QTreeWidgetItem configuration
		self.setFlags(Qt.ItemIsDragEnabled | Qt.ItemIsEnabled) # we can move a contact
		self.parent = parent
		self.jid = jid
		self.name = jid
		self.setStatus(show)
		self.connection = con
		
	def setName(self, name):
		if name:
			self.name = name
			self.setText(0, name)

	def setStatus(self, show):
		self.show = show
		fileShow = "interface/resource/icons/status/" + str(self.show) + ".png"
		self.setIcon(0, QIcon(fileShow))
		
	def status(self):
		return status
		
	def __str__(self):
		return u'%s' % self.name
