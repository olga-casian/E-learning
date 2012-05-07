from PyQt4.QtGui import QWidget, QTextEdit, QVBoxLayout, QTreeWidget
from PyQt4.QtCore import SIGNAL, QSize, Qt
from PyQt4 import QtGui, QtCore
from PyQt4 import uic
import md5, webbrowser
import datetime

from constants import PATH_UI_MESSAGE
from ChatMembers import ChatMembers


class MessageTextEdit(QTextEdit):
	def __init__(self, parent):
		QtGui.QTextEdit.__init__(self, parent)
		self.parent = parent
		self.setMaximumSize(QSize(16777215, 50))

	def keyPressEvent(self, event):
		if event.key() == QtCore.Qt.Key_Return:
			text = self.toPlainText().strip()
			if text:
				self.parent.sendMessage(text)
				self.setText("")
			return
		return QTextEdit.keyPressEvent(self, event)
		

class MessageDialog(QWidget):	
	def __init__(self, con, jidTo, buddyList, parent=None):
		super(MessageDialog, self).__init__(parent)
		
		self.jidTo = []
		self.initialJidTo = []
		#self.nameTo = []
		self.jidTo.append(jidTo)
		#self.nameTo.append(nameTo)
		self.initialJidTo.append(jidTo)
		self.con = con
		self.buddyList = buddyList
		
		# loading .ui
		uic.loadUi(PATH_UI_MESSAGE, self)
		self.updateDialog()
		self.btn_update.hide()
		self.chb_members.hide()
		
		# ading QTextEdit
		self.messageTextEdit = MessageTextEdit(self)
		self.vlt_message_widget.insertWidget(-1, self.messageTextEdit)		
		self.tbr_browser.setPlainText("")
		#self.messageTextEdit.setOpenLinks(False)
		self.messageTextEdit.setFocus()
		
		# chat members
		self.chatMembers = ChatMembers(self)
		self.vlt_members.insertWidget(1, self.chatMembers)
		self.chatMembers.setConnection(self.con)
		self.chatMembers.constructList()
		self.showMembersBuddies(True)

		self.connect(self.tbr_browser, SIGNAL("anchorClicked(QUrl)"), self.openLink)
		self.connect(self.btn_members, SIGNAL("toggled(bool)"), self.showMembersLayout)		
		self.connect(self.chb_members, SIGNAL("toggled(bool)"), self.showMembersBuddies)
		self.connect(self.btn_update, SIGNAL("clicked()"), self.chatMembers.updateMembers)	
		
	def updateDialog(self):
		if len(self.jidTo) is 1:
			if self.initialJidTo == self.jidTo: # if person is the same
				self.setWindowTitle("Chat with " + self.con.getName(self.jidTo[0]))
			else:
				for child in self.chatMembers.buddies.values():
					if child.jid in self.initialJidTo: # new person found in roster
						child.setState(Qt.Checked)
						self.showMembersBuddies(True)						
					elif child.jid in self.jidTo: # old
						child.setState(Qt.Unchecked)
						self.showMembersBuddies(True)
					else:
						child.setState(Qt.Unchecked)						
				self.close()
				self.buddyList.newDialog(self.jidTo)
				self.jidTo[0] = self.initialJidTo[0] 
		else:
			self.setWindowTitle("Group chat (" + str(len(self.jidTo)) + ")")
		
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
		
	def receiveMessage(self, msg):
		time = str(datetime.datetime.now().strftime("%H:%M:%S"))
		message = """\n<span style="color: darkblue">[%s] <strong>%s:</strong></span> %s""" % (time, self.nameTo[0], msg)
		self.tbr_browser.append(message)
		self.emit(SIGNAL("debug"), "message form " + self.nameTo[0] + ":\n" + msg + "\n\n")

	def sendMessage(self, text):
		time = str(datetime.datetime.now().strftime("%H:%M:%S"))
		message = """\n<span style="color: darkred">[%s] <strong>%s:</strong></span> %s""" % (time, self.tr("Me"), text)
		self.tbr_browser.append(message)
		self.con.send_message(self.jidTo[0], text)
		self.messageTextEdit.clear()

	def openLink(self, url):
		webbrowser.open(url.toString())
