from PyQt4.QtGui import QWidget, QTextEdit, QPushButton, QMenu, QImageWriter, QAction, QFileDialog
from PyQt4.QtCore import SIGNAL, QSize, Qt, QDir
from PyQt4 import QtGui, QtCore
from PyQt4 import uic
import re
import os

from constants import PATH_UI_MESSAGE
from ChatMembers import ChatMembers
from Multimedia import Canvas


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
	def __init__(self, con, jidTo, buddyList, parent = None, nick = None):
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
		self.nick = nick
		
		# loading .ui
		uic.loadUi(PATH_UI_MESSAGE, self)
		self.dialogTitle()
		self.btn_update.hide()
		self.chb_members.hide()
		
		# ading QTextEdit
		self.messageTextEdit = MessageTextEdit(self)
		self.vlt_message_widget.insertWidget(-1, self.messageTextEdit)		
		self.tbr_browser.setPlainText("")
		self.messageTextEdit.setFocus()
		
		# chat members		
		if self.nick is None:
			self.chatMembers = ChatMembers(self)
			self.vlt_members.insertWidget(1, self.chatMembers)
			self.chatMembers.setConnection(self.con)
			
			if len(self.jidTo) is 1:
				self.chatMembers.constructMessageList()
			else:
				self.chatMembers.constructMUCList()
				
			self.showMembersBuddies(True)
			
			self.connect(self.btn_update, SIGNAL("clicked()"), self.chatMembers.updateMembers)
		else:
			# never show chat members if it is a privite chat with muc member
			self.btn_members.hide()

		# multimedia
		self.saveAsActs = []
		self.canvas = Canvas(self)
		self.vlt_top.insertWidget(1, self.canvas.scribbleArea)
		self.showMultimedia(False)
		self.connect(self.btn_color, SIGNAL("clicked()"), self.canvas.penColor)
		self.connect(self.btn_width, SIGNAL("clicked()"), self.canvas.penWidth)
		self.connect(self.btn_add, SIGNAL("clicked()"), self.canvas.add)
		self.connect(self.btn_undo, SIGNAL("clicked()"), self.canvas.undo)
		self.connect(self.btn_clear, SIGNAL("clicked()"), self.canvas.scribbleArea.clearImage)
		
		menu_save = QMenu(self)
		menu_save.addAction("&First Item")
		menu_save.addAction("&Second Item")
		menu_save.addAction("&Third Item")
		menu_save.addAction("F&ourth Item")
		self.btn_save.setMenu(menu_save)

		newAction = menu_save.addAction("Save &image As...")
		subMenu_image = QMenu("Popup Submenu", self)
		for format in QtGui.QImageWriter.supportedImageFormats():
			format = str(format)
			text = "." + format.lower()
			action = QtGui.QAction(text, self, triggered=self.saveFile)
			action.setData(format)
			self.saveAsActs.append(action)
		for action in self.saveAsActs:
			subMenu_image.addAction(action)
		newAction.setMenu(subMenu_image)	
        
		self.connect(self.btn_members, SIGNAL("toggled(bool)"), self.showMembersLayout)		
		self.connect(self.chb_members, SIGNAL("toggled(bool)"), self.showMembersBuddies)		
		self.connect(self.btn_multimedia, SIGNAL("toggled(bool)"), self.showMultimedia)
	
	def saveFile(self):
		# opens dialog to save file with selected file type
		fileFormat = self.sender().data()
		initialPath = QDir.currentPath() + '/untitled.' + fileFormat
		fileName = QFileDialog.getSaveFileName(self, 
			"Save As...", initialPath,
			".%s Files (*.%s);;All Files (*)" % (fileFormat.lower(), fileFormat))
		if fileName:
			return self.canvas.scribbleArea.saveImage(fileName, fileFormat)
		return False
	
	def showMultimedia(self, checked):
		if checked:
			self.canvas.scribbleArea.show()
			self.btn_color.show()
			self.btn_width.show()
			self.btn_save.show()
			self.btn_add.show()
			self.btn_undo.show()
			self.btn_clear.show()
			self.btn_canvas_session.show()
			self.btn_audio_session.show()
			self.btn_mute.show()
		else:
			self.canvas.scribbleArea.hide()
			self.btn_color.hide()
			self.btn_width.hide()
			self.btn_save.hide()
			self.btn_add.hide()
			self.btn_undo.hide()
			self.btn_clear.hide()
			self.btn_canvas_session.hide()
			self.btn_audio_session.hide()
			self.btn_mute.hide()

	def dialogTitle(self):
		if len(self.jidTo) is 1:
			if self.nick:
				mucPattern = """([\w\-\|][\w\-\.\|]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4})/[\w\-\|][\w\-\.\|]*"""
				group = re.findall(mucPattern, self.jidTo[0])				
				self.setWindowTitle("Chat with " + self.nick + " from " + group[0]) 
			else:
				self.setWindowTitle("Chat with " + self.con.getName(self.jidTo[0]))
		else:
			self.setWindowTitle("Group chat (" + str(len(self.jidTo)) + ")")	
			
	def updateDialog(self):
		if len(self.jidTo) is 1:
			if self.initialJidTo != self.jidTo: # if person is new					
				initialJid = self.setCheckboxes()
				self.chb_members.setChecked(False)
				self.showMembersBuddies(False)
				self.close()
				
				self.buddyList.newDialog(self.jidTo[0])
				
				# restore initial jidTo
				self.jidTo = []
				for el in initialJid:
					self.jidTo.append(unicode(el))
				self.jidTo.append(self.con.jabberID)
				self.jidTo = sorted(self.jidTo)
		else:
			self.jidTo.append(self.con.jabberID)
			if not self.oldMUC(): # if selected people are new
				initialJid = self.setCheckboxes()		
				self.jidTo = sorted(self.jidTo)
				
				# create or join group (always include our jid too)
				if not self.buddyList.MUCExists(self.jidTo):
					self.con.createMUC(self.jidTo)
				
				self.buddyList.newMUCItem(self.jidTo)
				self.buddyList.newMUCDialog(self.jidTo)
				
				# restore initial jidTo
				self.jidTo = []
				for el in initialJid:
					self.jidTo.append(unicode(el))
				self.chb_members.setChecked(False)
				self.showMembersBuddies(False)
				self.close()
			
	def oldMUC(self):
		# True - elements in self.initialJidTo match ones in self.jidTo, 
		# False - otherwise
		match = 0
		for initJid in self.initialJidTo:
			for jid in self.jidTo:
				if initJid == jid:
					match = match + 1
				if len(self.jidTo) == len(self.initialJidTo) == match:
					return True
		return False
			
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
