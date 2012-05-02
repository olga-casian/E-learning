from PyQt4.QtGui import QWidget, QTextEdit, QVBoxLayout
from PyQt4.QtCore import SIGNAL
from PyQt4 import QtCore, QtGui
from PyQt4 import uic
import md5, webbrowser
import datetime

from constants import PATH_UI_MESSAGE


class MessageTextEdit(QTextEdit):
	def __init__(self, parent):
		QtGui.QTextEdit.__init__(self, parent)
		self.parent = parent
		self.setMaximumSize(QtCore.QSize(16777215, 50))

	def keyPressEvent(self, event):
		if event.key() == QtCore.Qt.Key_Return:
			text = self.toPlainText().strip()
			print "'" + text + "'"
			if text:
				self.parent.sendMessage(text)
				self.setText("")
		return QTextEdit.keyPressEvent(self, event)
		

class MessageDialog(QWidget):	
	def __init__(self, con, jidTo, nameTo, parent=None):
		super(MessageDialog, self).__init__(parent)
		
		self.jid = jidTo
		self.name = nameTo
		self.con = con
		
		# loading .ui
		uic.loadUi(PATH_UI_MESSAGE, self)
		self.setWindowTitle("Chat with " + self.name)
		
		# ading QTextEdit
		self.messageTextEdit = MessageTextEdit(self)
		self.verticalLayout.addWidget(self.messageTextEdit)
		
		self.tbr_browser.setPlainText("")
		#self.messageTextEdit.setOpenLinks(False)

		self.messageTextEdit.setFocus()

		self.connect(self.tbr_browser, SIGNAL("anchorClicked(QUrl)"), self.openLink)

	def receiveMessage(self, msg):
		time = str(datetime.datetime.now().strftime("%H:%M:%S"))
		message = """\n<span style="color: darkblue">[%s] <strong>%s:</strong></span> %s""" % (time, self.name, msg)
		self.tbr_browser.append(message)
		self.emit(SIGNAL("debug"), "message form " + self.name + ":\n" + msg + "\n\n")

	def sendMessage(self, text):
		time = str(datetime.datetime.now().strftime("%H:%M:%S"))
		message = """\n<span style="color: darkred">[%s] <strong>%s:</strong></span> %s""" % (time, self.tr("Me"), text)
		self.tbr_browser.append(message)
		self.con.send_message(self.jid, text)
		self.messageTextEdit.clear()

	def openLink(self, url):
		webbrowser.open(url.toString())
