from PyQt4.QtCore import SIGNAL
import datetime

from AbstractDialog import AbstractDialog


class MessageDialog(AbstractDialog):	
	def __init__(self, con, jidTo, buddyList, parent = None, nick = None):
		AbstractDialog.__init__(self, con, jidTo, buddyList, nick, parent)
		
	def receiveMessage(self, msg):
		time = str(datetime.datetime.now().strftime("%H:%M:%S"))
		if self.nick:
			message = """\n<span style="color: darkblue">[%s] <strong>%s:</strong></span> %s""" % (time, self.nick, msg)
		else:
			message = """\n<span style="color: darkblue">[%s] <strong>%s:</strong></span> %s""" % (time, self.con.getName(self.jidTo[0]), msg)
		self.tbr_browser.append(message)
		self.emit(SIGNAL("debug"), "message form " + self.con.getName(self.jidTo[0]) + ":\n" + msg + "\n\n")

	def sendMessage(self, text):
		time = str(datetime.datetime.now().strftime("%H:%M:%S"))
		message = """\n<span style="color: darkred">[%s] <strong>%s:</strong></span> %s""" % (time, self.tr("Me"), text)
		self.tbr_browser.append(message)
		self.con.sendMessage(self.jidTo[0], text)
		self.messageTextEdit.clear()
		
	def sendCanvasStroke(self, d, stroke, stroke_width):
		self.con.sendCanvasStroke("chat", self.jidTo[0], d, stroke, stroke_width)
		
	def CanvasStroke(self, d, stroke, stroke_width):
		self.showMultimedia(True)
		#print "======private\n", d, stroke, stroke_width, "======\n"
		self.canvas.scribbleArea.draw(d, stroke, stroke_width)
