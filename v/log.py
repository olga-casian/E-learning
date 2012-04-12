import platform
import locale
import datetime
import time
from os import path, sep
import traceback
import threading
	
class Synchronized(object):	
	def __init__(self, *args):
		self.lock = threading.Lock()
		
	def __call__(self, f):
		def lockedfunc(*args, **kwargs):
			try:
				self.lock.acquire()
				try:
					return f(*args, **kwargs)
				except Exception, e:
					raise
			finally:
				self.lock.release()
		return lockedfunc


class Log(object):
	def __init__(self, path = path.expanduser('~'), fileName = 'test.log', calledFunc = True, 
				treadTrack = True, writeVerbosity = 'CRITICAL'):
		self.verbosity_dict = {'DEBUG': 1, 'INFO': 2, 'WARNING': 3, 'ERROR': 4, 'CRITICAL': 5}
		
		self.writeVerbosity = self.verbosity_dict[writeVerbosity]
		self.calledFunc = calledFunc
		self.treadTrack = treadTrack
		if path is '': self.fullPath = fileName
		else: self.fullPath = path + sep + fileName #os.path.join('sadasd','asdasd')
		#print type(self.fullPath)
		#print self.fullPath
		
		try:
			if self.check_size() is False:
				self.clear_log()
		except OSError:
			print '+++++ unable to get file size: no file or file is inaccessible +++++'
		
		self.write_system_report()
		
	def get_timestamp(self):
		return str(datetime.datetime.now().strftime("%H:%M:%S.%f"))

	def turn_off(self):
		self.writeVerbosity = 6
		print '+++++ logging turned off +++++'
		
	def turn_on(self, writeVerbosity):
		self.writeVerbosity = self.verbosity_dict[writeVerbosity]
		print '+++++ logging turned on with level of verbosity {} +++++'.format(writeVerbosity)
		
	def write_system_report(self):
		string = ''
		localtime   = time.localtime()
		timeString  = time.strftime("==========================%Y-%m-%d %H:%M:%S ", localtime)
	
		timezone	= -(time.altzone if time.localtime().tm_isdst else time.timezone)
		timeString += "Z" if timezone == 0 else "+" if timezone > 0 else "-"
		timeString += time.strftime("%H:%M==========================", time.gmtime(abs(timezone)))
		string += timeString				
		string += "\ndefault locale: " + locale.getdefaultlocale()[0] + ' ' \
			+ locale.getdefaultlocale()[1]

		string += "\nhome directory: " + path.expanduser('~')
		string += "\nlog file path:\t" + self.fullPath		
			
		string += "\nmachine:\t" + platform.machine()
		string += "\narchitecture:\t" + platform.architecture()[0] + ' ' \
			+ platform.architecture()[1]
		string += "\nplatform:\t" + platform.platform()
		
		try:
			self.write_file('\n\n\n' + string + '\n')
		except:
			print '+++++ unable to write to file +++++'
			
		print string + '\n'	
		
	def write_log(self, list, verbosity = 'DEBUG', comment = ''):
		if self.verbosity_dict[verbosity] >= self.writeVerbosity:
			tmp = ''	
			if type(list) is str or int: 
				tmp = str(list)
			else:
				for el in list:
					tmp += str(el) + ' '
			
			string = self.get_timestamp() + '\t'			
			if self.calledFunc is True:
				stack = traceback.extract_stack()
				funcName = stack[len(stack)-2][2]
				string += funcName + '\t'
			if self.treadTrack is True:
				threadID = threading.currentThread().name
				string += threadID + '\t'
			string += comment + '\t' + tmp 
			
			try:			
				self.write_file('\n' + string)
			except:
				print '+++++ unable to write to file +++++'
			
			print string
		elif self.writeVerbosity == 6:
			print '+++++ failed to write: logging turned off +++++'
		else: print '+++++ log have not been written: too low level of verbosity +++++' 
	
	@Synchronized()
	def write_file(self, string):	
		fh = open(self.fullPath, 'a')
		fh.write(string)
		fh.close()
		
	@Synchronized()
	def check_size(self):
		bytes = path.getsize(self.fullPath)
		bytes = float(bytes)
		if bytes >= 1048576:
			megabytes = bytes / 1048576
			size = '+++++ file is %.2f M +++++' % megabytes
		elif bytes >= 1024:
			kilobytes = bytes / 1024
			size = '+++++ file is %.2f K +++++' % kilobytes
		else:
			size = '+++++ file is %.2f b +++++' % bytes
		print size
		if bytes >= 1024 : return False
		else: return True
		
	@Synchronized()
	def clear_log(self):
		print '+++++ clearing logs +++++' 
		fh = open(self.fullPath, 'w')
		fh.write('')
		fh.close()
		
def worker(ver, log):
	# bool
	log.write_log((True, False), 'DEBUG', 'bool')
	log.write_log(True, verbosity = 'INFO', comment = 'bool')
	# int
	log.write_log((232,23,23,34), verbosity = 'DEBUG', comment = 'int')
	log.write_log(23, verbosity = 'INFO', comment = 'int')
	# str
	log.write_log(('3434', '3434'), verbosity = 'WARNING', comment = 'str')
	log.write_log('3433434', verbosity = 'CRITICAL', comment = 'str')
	
		
def main():
	log = Log(fileName = 'test.log', writeVerbosity = 'DEBUG')

	# bool
	log.write_log((True, False), 'DEBUG', 'bool')
	log.write_log(True, verbosity = 'INFO', comment = 'bool')
	# int
	log.write_log((232,23,23,34), verbosity = 'DEBUG', comment = 'int')
	log.write_log(23, verbosity = 'INFO', comment = 'int')
	# str
	log.write_log(('3434', '3434'), verbosity = 'WARNING', comment = 'str')
	log.write_log('3433434', verbosity = 'CRITICAL', comment = 'str')
	# dict
	log.turn_off()
	log.write_log(({'a':1, 'b':2}, {'a':1, 'b':2}), verbosity = 'WARNING', comment = 'dict')
	log.write_log({'a':1, 'b':2}, verbosity = 'CRITICAL', comment = 'dict')
	log.turn_on('DEBUG')
	
	t = threading.Thread(target=worker, args=(True, log))
	t.start()
	
	# set
	log.write_log(((['e', 't']), (['o', 'k'])), verbosity = 'WARNING', comment = 'set')
	log.write_log((['e', 't']), verbosity = 'CRITICAL', comment = 'set')
	# lists
	log.write_log((['e', 't'], ['o', 'k']), verbosity = 'WARNING', comment = 'lists')
	log.write_log(['e', 't'], verbosity = 'CRITICAL', comment = 'lists')
	# tuples
	log.write_log((('e', 't'), ('o', 'k')), verbosity = 'WARNING', comment = 'tuples')
	log.write_log(('e', 't'), verbosity = 'CRITICAL', comment = 'tuples')
	
if __name__ == "__main__":
	main()
