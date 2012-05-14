from PyQt4.QtCore import SIGNAL
import datetime

from AbstractDialog import AbstractDialog


class MUCDialog(AbstractDialog):	
	def __init__(self, con, jidTo, buddyList, parent = None):
		AbstractDialog.__init__(self, con, jidTo, buddyList, parent)

	def sendMessage(self, text):
		time = str(datetime.datetime.now().strftime("%H:%M:%S"))
		message = """\n<span style="color: darkred">[%s] <strong>%s:</strong></span> %s""" % (time, self.tr("Me"), text)
		self.tbr_browser.append(message)
		self.con.sendMUCMessage(self.jidTo, text)
		self.messageTextEdit.clear()
		
	def receiveMessage(self, nick, msg):
		time = str(datetime.datetime.now().strftime("%H:%M:%S"))
		message = """\n<span style="color: darkblue">[%s] <strong>%s:</strong></span> %s""" % (time, nick, msg)#(time, self.con.getName(self.jidTo[0]), msg)
		self.tbr_browser.append(message)
		self.emit(SIGNAL("debug"), "MUC message form " + self.con.getName(self.jidTo[0]) + ":\n" + msg + "\n\n")
