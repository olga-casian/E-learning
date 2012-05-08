from PyQt4.QtGui import QWidget, QTextEdit
from PyQt4.QtCore import SIGNAL, QSize, Qt
from PyQt4 import QtGui, QtCore
from PyQt4 import uic

from constants import PATH_UI_MESSAGE
from ChatMembers import ChatMembers


class MessageTextEdit(QTextEdit):
	def __init__(self, parent):
		QtGui.QTextEdit.__init__(self, parent)
		self.parent = parent
		self.setMaximumSize(QSize(16777215, 50))

	def keyPressEvent(self, event):
		if event.key() == Qt.Key_Return:
			text = self.toPlainText().strip()
			if text:
				self.parent.sendMessage(text)
				self.setText("")
			return
		return QTextEdit.keyPressEvent(self, event)
	
		
class AbstractDialog(QWidget):
	def __init__(self, con, jidTo, buddyList, parent = None):
		super(AbstractDialog, self).__init__(parent)

		self.jidTo = []
		self.initialJidTo = []
		
		if len(list(jidTo)) > 1 and len(jidTo[0]) > 1:
			for el in list(jidTo):
				self.jidTo.append(el)
		else: self.jidTo.append(jidTo)
		
		for el in self.jidTo:
			self.initialJidTo.append(el)
			
		self.con = con
		self.buddyList = buddyList
		
		# loading .ui
		uic.loadUi(PATH_UI_MESSAGE, self)
		self.dialogTitle()
		self.btn_update.hide()
		self.chb_members.hide()
		
		# ading QTextEdit
		self.messageTextEdit = MessageTextEdit(self)
		self.vlt_message_widget.insertWidget(-1, self.messageTextEdit)		
		self.tbr_browser.setPlainText("")
		#self.tbr_browser.setOpenLinks(True)
		self.messageTextEdit.setFocus()
		
		# chat members
		self.chatMembers = ChatMembers(self)
		self.vlt_members.insertWidget(1, self.chatMembers)
		self.chatMembers.setConnection(self.con)
		
		if len(self.jidTo) is 1:
			self.chatMembers.constructMessageList()
		else:
			self.chatMembers.constructMUCList()
			
		self.showMembersBuddies(True)

		#self.connect(self.tbr_browser, SIGNAL("anchorClicked(QUrl)"), self.openLink)
		self.connect(self.btn_members, SIGNAL("toggled(bool)"), self.showMembersLayout)		
		self.connect(self.chb_members, SIGNAL("toggled(bool)"), self.showMembersBuddies)
		self.connect(self.btn_update, SIGNAL("clicked()"), self.chatMembers.updateMembers)

	def dialogTitle(self):
		if len(self.jidTo) is 1:
			self.setWindowTitle("Chat with " + self.con.getName(self.jidTo[0]))
		else:
			self.setWindowTitle("Group chat (" + str(len(self.jidTo)) + ")")	
			
	def updateDialog(self):
		if len(self.jidTo) is 1:
			if self.initialJidTo != self.jidTo: # if person is new					
				initialJid = self.setCheckboxes()
				self.close()
				
				self.buddyList.newDialog(self.jidTo[0])
				
				# restore initial jidTo
				self.jidTo[0] = initialJid[0]
		else:
			if self.initialJidTo != self.jidTo: # if selected people are new
				initialJid = self.setCheckboxes()
				self.close()
				
				self.buddyList.newListItem(self.jidTo)
				self.buddyList.newMUC(self.jidTo)
				
				# restore initial jidTo
				self.jidTo = []
				for el in initialJid:
					self.jidTo.append(el)
			
	def setCheckboxes(self):
		initialJid = []
		for child in self.chatMembers.buddies.values():
			if child.jid in self.initialJidTo and child.jid not in self.jidTo: # old desselected
				child.setState(Qt.Checked)
				initialJid.append(child.jid)
			elif child.jid in self.initialJidTo: # old
				child.setState(Qt.Checked)
				initialJid.append(child.jid)
			elif child.jid in self.jidTo: # new person found in roster
				child.setState(Qt.Unchecked)
			else:
				child.setState(Qt.Unchecked)
		self.showMembersBuddies(True)
		return initialJid
			
	def showMembersLayout(self, checked):
		if checked:
			self.chatMembers.show()
			self.btn_update.show()
			self.chb_members.show()
		else:
			self.chatMembers.hide()
			self.btn_update.hide()
			self.chb_members.hide()
			
	def showMembersBuddies(self, checked):
		self.chatMembers.showMembersBuddies(self.chb_members.isChecked())

	#def openLink(self, url):
	#	webbrowser.open(url.toString())
