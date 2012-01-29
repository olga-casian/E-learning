#!/usr/bin/env python

# These are only needed for Python v2 but are harmless for Python v3
import sip
sip.setapi('QString', 2)
sip.setapi('QVariant', 2)

import sys
from PyQt4 import QtCore, QtGui, uic


class ScribbleArea(QtGui.QWidget):
    """
    class adds QImage to MyMainWindow, overrides parent's event functions
    """
    def __init__(self, parent=None):
        super(ScribbleArea, self).__init__(parent)

        self.setAttribute(QtCore.Qt.WA_StaticContents)
        
        self.modified = False
        self.scribbling = False
       
        self.myPenWidth = 2
        self.myPenColor = QtGui.QColor(0, 85, 255) #QtCore.Qt.blue
        
        imageSize = QtCore.QSize()
        self.image = QtGui.QImage(imageSize, QtGui.QImage.Format_RGB32)
        self.lastPoint = QtCore.QPoint()

    def saveImage(self, fileName, fileFormat):
        # saves visible image
        visibleImage = self.image
        self.resizeImage(visibleImage, self.size())

        if visibleImage.save(fileName, fileFormat):
            self.modified = False
            return True
        else:
            return False

    def mousePressEvent(self, event):
#       print "self.image.width() = %d" % self.image.width()
#       print "self.image.height() = %d" % self.image.height()
#       print "self.image.size() = %s" % self.image.size()
#       print "self.size() = %s" % self.size()
#       print "event.pos() = %s" % event.pos()
        if event.button() == QtCore.Qt.LeftButton:
            self.lastPoint = event.pos()
            self.scribbling = True

    def mouseMoveEvent(self, event):
        if (event.buttons() & QtCore.Qt.LeftButton) and self.scribbling:
            self.drawLineTo(event.pos())
            print "event.pos() = ", event.x(), " ", event.y(), "-", \
				self.myPenWidth, "-", \
				self.myPenColor.red(), " ", \
				self.myPenColor.green(), " ", self.myPenColor.blue()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.scribbling:
            self.drawLineTo(event.pos())
            self.scribbling = False

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawImage(event.rect(), self.image)

    def resizeEvent(self, event):		
        self.resizeImage(self.image, event.size())

        super(ScribbleArea, self).resizeEvent(event)

    def resizeImage(self, image, newSize):
        if image.size() == newSize:
            return
            
        newImage = QtGui.QImage(newSize, QtGui.QImage.Format_RGB32)
        newImage.fill(QtGui.qRgb(255, 255, 255))
        painter = QtGui.QPainter(newImage)
        painter.drawImage(QtCore.QPoint(0, 0), image)
        #painter.drawImage(0, 0, image, 900, 900)
        
        self.image = newImage
        
    def drawLineTo(self, endPoint):
        painter = QtGui.QPainter(self.image)
        painter.setPen(QtGui.QPen(self.myPenColor, self.myPenWidth,
            QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
        painter.drawLine(self.lastPoint, endPoint)
        self.modified = True

        self.update()
        self.lastPoint = QtCore.QPoint(endPoint)

    def isModified(self):
        return self.modified

    def penColor(self):
        return self.myPenColor

    def penWidth(self):
        return self.myPenWidth
    
    def setPenColor(self, newColor):
        self.myPenColor = newColor

    def setPenWidth(self, newWidth):
        self.myPenWidth = newWidth


class MyMainWindow(QtGui.QMainWindow):	
	"""
	class for loading and extending .ui file generated in Qt Designer;
	has basic functionality of interface
	"""
	def __init__(self, parent=None):
		super(MyMainWindow, self).__init__(parent)
		
		self.saveAsActs = []
		
		# loading .ui
		uic.loadUi('project.ui', self)        

		# ading QImage
		self.scribbleArea = ScribbleArea(self)
		self.clearImage()
		"""
		self.scrollArea = QtGui.QScrollArea()
		self.scrollArea.setBackgroundRole(QtGui.QPalette.Dark)
		self.scrollArea.setWidget(self.scribbleArea)
		"""
		self.hlt_canvas_menu_buttons.addWidget(self.scribbleArea)

		# connect functions
		self.connect(self.btn_clear, QtCore.SIGNAL('clicked()'), self.clearImage)
		self.connect(self.btn_color, QtCore.SIGNAL('clicked()'), self.penColor)
		self.connect(self.btn_size, QtCore.SIGNAL('clicked()'), self.penWidth)
		
		# create menu bar
		self.createActions()
		self.createMenus()

	def penColor(self):
		# opens dialog to change pen color
		newColor = QtGui.QColorDialog.getColor(self.scribbleArea.penColor())
		if newColor.isValid():
			self.scribbleArea.setPenColor(newColor)

	def penWidth(self):
		# opens dialog to change pen width
		newWidth, ok = QtGui.QInputDialog.getInteger(self, "E-learning",
			"Select pen width:", self.scribbleArea.penWidth(), 1, 50, 1)
		if ok:
			self.scribbleArea.setPenWidth(newWidth)
			
	def clearImage(self):
		# clears image
		self.scribbleArea.image.fill(QtGui.qRgb(255, 255, 255))
		self.scribbleArea.modified = True
		self.scribbleArea.update()	
		
	def saveFile(self):
		# opens dialog to save file with selected file type
		fileFormat = self.sender().data()
		initialPath = QtCore.QDir.currentPath() + '/untitled.' + fileFormat
		fileName = QtGui.QFileDialog.getSaveFileName(self, "Save As", initialPath,
			"%s Files (*.%s);;All Files (*)" % (fileFormat.upper(), fileFormat))

		if fileName:
			return self.scribbleArea.saveImage(fileName, fileFormat)

		return False
        
	def createActions(self):
		# creates sub menus
		for format in QtGui.QImageWriter.supportedImageFormats():
			format = str(format)

			text = "." + format.lower()

			action = QtGui.QAction(text, self, triggered=self.saveFile)
			action.setData(format)
			self.saveAsActs.append(action)

		self.exitAct = QtGui.QAction("E&xit", self, shortcut="Ctrl+Q",
			triggered=self.close)

	def createMenus(self):
		# creates menus
		self.saveAsMenu = QtGui.QMenu("&Save As", self)
		for action in self.saveAsActs:
			self.saveAsMenu.addAction(action)

		fileMenu = QtGui.QMenu("&File", self)
		fileMenu.addMenu(self.saveAsMenu)
		fileMenu.addAction(self.exitAct)
		
		helpMenu = QtGui.QMenu("&Help", self)
		self.menuBar().addMenu(fileMenu)
		self.menuBar().addMenu(helpMenu)
        
        	
		
if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)
	myApp = MyMainWindow()
	myApp.show()
	sys.exit(app.exec_())
