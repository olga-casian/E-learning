#!/usr/bin/python
# -*- coding: utf-8 -*-

# These are only needed for Python v2 but are harmless for Python v3
import sip
sip.setapi('QString', 2)
sip.setapi('QVariant', 2)

import logging
import datetime
import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import SIGNAL, SLOT, QSettings, Qt
from PyQt4 import uic

import interface.resource.res
from BuddyList import BuddyList
from im import Client
from constants import SHOW, PATH_UI_MAIN, PATH_UI_CONNECTION, PATH_UI_LOGS, PATH_UI_ABOUT_PYTALK


class MainWindow(QMainWindow):	
	def __init__(self, parent=None):
		#QMainWindow.__init__(self, None, Qt.WindowStaysOnTopHint) # always on top
		super(MainWindow, self).__init__(parent)
		
		self.settings = QSettings("Dae-ekleN", "PyTalk")
		
		# add logs widget		
		QWidget.__init__(self)
		self.logsWidget = uic.loadUi(PATH_UI_LOGS)
		self.logsWidget.etx_logs.setReadOnly(True)
		
		# loading .ui
		uic.loadUi(PATH_UI_MAIN, self)
		
		# Set status Offline
		self.cmb_status_box.setCurrentIndex(5)
		self.cmb_status_box.setEnabled(False)
		self.eln_status_edit.hide()
		
		# connecting signals
		self.connect(self.cmb_status_box, SIGNAL("currentIndexChanged(int)"), self.statusUpdate)
		self.connect(self.eln_status_edit, SIGNAL("returnPressed()"), self.statusUpdate)
        
        # Set BuddyList
		self.BuddyList = BuddyList(self)
		self.vboxlayout.insertWidget(0, self.BuddyList)
		#self.connect(self.BuddyList, SIGNAL("rename"), self.addBuddy)
		
		# Connection
		self.act_connection.triggered.connect(self.showConnectDialog)
		#self.connect(self.act_deconnection, SIGNAL("triggered()"), self.disconnect)
		
		# View
		self.connect(self.act_away_buddies, SIGNAL("toogled()"), self.showAwayBuddies)
		self.connect(self.act_offline_buddies, SIGNAL("toogled()"), self.showOfflineBuddies)
		self.connect(self.act_away_buddies, SIGNAL("triggered()"), self.showAwayBuddies)
		self.connect(self.act_offline_buddies, SIGNAL("triggered()"), self.showOfflineBuddies)
		
		# Tools
		self.connect(self.act_logs, SIGNAL("triggered()"), self.showLogs)
		
		# About Dialogs
		self.connect(self.act_about_pytalk, SIGNAL("triggered()"), self.aboutPyTalk)
		self.connect(self.act_about_qt, SIGNAL("triggered()"), QApplication.instance(), SLOT("aboutQt()"))
		
	def aboutPyTalk(self):
		QDialog.__init__(self)
		self.aboutPyTalk = uic.loadUi(PATH_UI_ABOUT_PYTALK)
		self.aboutPyTalk.show()
		self.aboutPyTalk.raise_()
		
	def showConnectDialog(self):
		# opens connection dialog		
		QDialog.__init__(self)
		self.connectionDialog = uic.loadUi(PATH_UI_CONNECTION)
		self.connectionDialog.show()
		self.connect(self.connectionDialog, SIGNAL("accepted()"), self.connection)
		
		self.connectionDialog.eln_jid.setText(self.settings.value("jid", ""))
		self.connectionDialog.eln_pass.setText(self.settings.value("password", ""))

		"""
	def disconnect(self):
		self.act_connection.setEnabled(True)
		self.act_deconnection.setEnabled(False)
		self.eln_status_edit.hide()
		self.cmb_status_box.setEnabled(False)
		if self.im:
			self.im.stop()
			self.im = None
		#QApplication.instance().quit()
		"""

	def connection(self):		
		# settings for jid and pass
		#self.settings = QSettings("Dae-ekleN", "PyTalk")
		self.settings.setValue("jid", self.connectionDialog.eln_jid.text())
		self.settings.setValue("password", self.connectionDialog.eln_pass.text())
			
		# latest status and show
		self.clientJid = str(self.connectionDialog.eln_jid.text())
		self.settings.beginGroup(self.clientJid)
		self.latestShow = self.settings.value("latestShow", "") # text as in SHOW
		self.latestStatus = self.settings.value("latestStatus", "")
		self.settings.endGroup()
			
		# starting xmpp thread
		self.im = Client(self.connectionDialog.eln_jid.text(), self.connectionDialog.eln_pass.text(),
			self.latestShow, self.latestStatus)
		self.im.start()
			
		self.cmb_status_box.setItemText(5, "Please wait...")
			
		# connecting signals
		self.connect(self.im, SIGNAL("sessionStarted(PyQt_PyObject)"), self.sessionStarted)
		self.connect(self.im, SIGNAL("debug"), self.debug)
		self.connect(self.im, SIGNAL("presence(PyQt_PyObject)"), self.BuddyList.presence)
		self.connect(self.im, SIGNAL("message"), self.BuddyList.message)
		
	def sessionStarted(self, roster_keys):
		self.act_connection.setEnabled(False)
		self.act_deconnection.setEnabled(True)
        
		# construct contact list	
		self.BuddyList.setConnection(self.im)
		#store roster in settings
		self.settings.beginGroup(self.clientJid)
		self.settings.setValue("roster", roster_keys)
		self.settings.endGroup()
		self.BuddyList.constructList(roster_keys)
		self.showAwayBuddies()
		self.showOfflineBuddies()
	
		# restore show and status
		self.eln_status_edit.show()
		self.eln_status_edit.setText(self.latestStatus)
		
		self.cmb_status_box.setItemText(5, "Offline")
		if self.latestShow == "": self.cmb_status_box.setCurrentIndex(SHOW.index('available'))
		else: self.cmb_status_box.setCurrentIndex(SHOW.index(self.latestShow))
		self.cmb_status_box.setEnabled(True)
	
	def statusUpdate(self):
		# update settings
		self.settings.beginGroup(self.clientJid)
		self.settings.setValue("latestShow", SHOW[self.cmb_status_box.currentIndex()])
		self.settings.setValue("latestStatus", self.eln_status_edit.text())
		self.settings.endGroup()
		self.debug("new presence set. show: '" + SHOW[self.cmb_status_box.currentIndex()] +
			"'; status: '" + self.eln_status_edit.text() + "'\n\n")
		
		self.im.changeStatus(self.cmb_status_box.currentIndex(), self.eln_status_edit.text())
            
	def showLogs(self):
		self.logsWidget.show()
		self.logsWidget.raise_()
		
	def debug(self, message):
		self.logsWidget.etx_logs.append(datetime.datetime.now().strftime("[%H:%M:%S]")+":\n" + message)
	
	def showAwayBuddies(self):	
		self.BuddyList.showAwayBuddies(not self.act_away_buddies.isChecked())
		
	def showOfflineBuddies(self):
		self.BuddyList.showOfflineBuddies(not self.act_offline_buddies.isChecked())

if __name__ == "__main__":
	# Setup logging
	#logging.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')
	
	app = QApplication(sys.argv)
	window = MainWindow()
	window.show()
	sys.exit(app.exec_())
