from PyQt4.QtCore import SIGNAL
import datetime

from AbstractDialog import AbstractDialog


class MessageDialog(AbstractDialog):	
	def __init__(self, con, jidTo, buddyList, parent = None):
		AbstractDialog.__init__(self, con, jidTo, buddyList, parent)
		
	def receiveMessage(self, msg):
		time = str(datetime.datetime.now().strftime("%H:%M:%S"))
		message = """\n<span style="color: darkblue">[%s] <strong>%s:</strong></span> %s""" % (time, self.con.getName(self.jidTo[0]), msg)
		self.tbr_browser.append(message)
		self.emit(SIGNAL("debug"), "message form " + self.con.getName(self.jidTo[0]) + ":\n" + msg + "\n\n")

	def sendMessage(self, text):
		time = str(datetime.datetime.now().strftime("%H:%M:%S"))
		message = """\n<span style="color: darkred">[%s] <strong>%s:</strong></span> %s""" % (time, self.tr("Me"), text)
		self.tbr_browser.append(message)
		self.con.send_message(self.jidTo[0], text)
		self.messageTextEdit.clear()
