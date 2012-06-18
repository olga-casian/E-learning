import time


class Point():
	"""
	class for storing point data for history
	"""
	def __init__(self, x, y, w, cR, cG, cB):
		self.x = x
		self.y = y
		self.w = w
		self.cR = cR
		self.cG = cG
		self.cB = cB
		self.time = time.time()
		
	def getX(self):
		return self.x
	
	def getY(self):
		return self.y
		
	def getW(self):
		return self.w
		
	def getCR(self):
		return self.cR
	
	def getCG(self):
		return self.cG
		
	def getCB(self):
		return self.cB
		
	def getTime(self):
		return self.time
		
	def getAll(self):
		return self.x, self.y, self.w, self.cR, self.cG, self.cB, self.time


class History():
	"""
	class for storing history of strokes (as stack) abd points (see Point class); 
	used for undo
	"""
	def __init__(self):
		self.history = []
		
	def newPoint(self, x, y, w, cR, cG, cB):
		latest = self.history.pop()
		point = Point(x, y, w, cR, cG, cB)
		latest.append(point)
		self.history.append(latest)
		
	def newStroke(self, x, y, w, cR, cG, cB):
		point = Point(x, y, w, cR, cG, cB)
		self.history.append([point])
		
	def removeLast(self):
		if len(self.history) > 0:
			self.history.pop()
			return True
		else: return False
	
	def clear(self):
		self.history = []	
		
	def printHistory(self):
		print '=====================NEW PRINT======================================='
		for stroke in self.history:
			print '+++++++++++++++++++++NEW STROKE++++++++++++++++++++\n'
			for point in stroke:
				print point.getAll()
		
	def printXEP113(self):
		"""
		red triangle:
		d='M 100 100 L 300 100 200 300 100 100' stroke='#ff0000' stroke-width='1'
		"""
		print '=====================NEW PRINT======================================='
		for stroke in self.history:
			print '+++++++++++++++++++++NEW STROKE++++++++++++++++++++\n'
			d = ""
			for point in stroke:
				d += str(point.getX()) + " " + str(point.getY()) + " "
			stroke = str(point.getCR()) + str(point.getCG()) + str(point.getCB())
			stroke_width = str(point.getW())
			line = "d='" + d[:-1] + "' stroke='#" + stroke + "' stroke-width='" + stroke_width + "'"
			print line
			 
	def getLastXEP113(self):
		"""
		red triangle:
		d='M 100 100 L 300 100 200 300 100 100' stroke='#ff0000' stroke-width='1'
		"""
		if len(self.history) > 0:
			stroke = self.history[len(self.history)-1]
			d = ""
			for point in stroke:
				d += str(point.getX()) + " " + str(point.getY()) + " "
			stroke = str(point.getCR()) + " " +  str(point.getCG()) + " " +  str(point.getCB())
			stroke_width = str(point.getW())
			#line = "d='" + d[:-1] + "' stroke='#" + stroke + "' stroke-width='" + stroke_width + "'"
			return d, stroke, stroke_width
