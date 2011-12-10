#!/usr/bin/env python
# encoding: utf-8
"""
log.py

Created by Thomas Mangin on 2011-11-29.
Copyright (c) 2011 Exa Networks. All rights reserved.
"""

#!/usr/bin/env python
# encoding: utf-8
"""
utils.py

Created by Thomas Mangin on 2009-09-06.
Copyright (c) 2009-2011 Exa Networks. All rights reserved.
"""

import os
import sys
import time
import logging
import logging.handlers

from threading import Lock

from .configuration import Configuration,log

def hex_string (value):
	return '%s' % [(hex(ord(_))) for _ in value]

def single_line (value):
	return '[%s]' % value.replace('\r\n','\\r\\n')


class LazyFormat (object):
	def __init__ (self,prefix,format,message):
		self.prefix = prefix
		self.format = format
		self.message = message
	
	def __str__ (self):
		if self.format:
			return self.prefix + self.format(self.message)
		return self.prefix + self.message
	
	def split (self,c):
		return str(self).split(c)

class _Logger (object):
	DEBUG = Configuration().DEBUG
	
	_instance = None
	_syslog = None

	_inserted = 0
	_max_history = 20
	_history = []
	_lock = Lock()
	
	_config = ''
	_pid = os.getpid()
	
	# we use os.pid everytime as we may fork and the class is instance before it

	def history (self):
		with self._lock:
			return '\n'.join(self._format(*_) for _ in self._history)

	def _record (self,timestamp,level,source,message):
		with self._lock:
			self._history.append((timestamp,level,source,message))
			if len(self._history) > self._max_history:
				self._history.pop(0)

	def _format (self,timestamp,level,source,message):
		now = time.strftime('%a, %d %b %Y %H:%M:%S',timestamp)
		return '%s %-8s %-6d %-13s %s' % (now,level,self._pid,source,message)

	def _prefixed (self,level,source,message):
		ts = time.localtime()
		self._record(ts,level,source,message)
		return self._format(ts,level,source,message)

	def __init__ (self):
		destination = Configuration().SYSLOG
		if destination is None:
			return

		try:
			if destination == '':
				if sys.platform == 'darwin':
					address = '/var/run/syslog'
				else:
					address = '/dev/log'
				if not os.path.exists(address):
					address = ('localhost', 514)
				handler = logging.handlers.SysLogHandler(address)
			elif destination.lower().startswith('host:'):
				# If the address is invalid, each syslog call will print an error.
				# See how it can be avoided, as the socket error is encapsulated and not returned
				address = (destination[5:].strip(), 514)
				handler = logging.handlers.SysLogHandler(address)
			else:
				handler = logging.handlers.RotatingFileHandler(destination, maxBytes=5*1024*1024, backupCount=5)
			self._syslog = logging.getLogger()
			self._syslog.setLevel(logging.DEBUG)
			self._syslog.addHandler(handler)
		except IOError,e :
			self.critical('Can not use SYSLOG, failing back to stdout')

	def debug (self,message,source='',level='DEBUG'):
		for line in message.split('\n'):
			if self._syslog:
				self._syslog.debug(self._prefixed(level,source,line))
			elif self.DEBUG.LOG >=log.LOG_DEBUG:
				print self._prefixed(level,source,line)
				sys.stdout.flush()

	def info (self,message,source='',level='INFO'):
		for line in message.split('\n'):
			if self._syslog:
				self._syslog.info(self._prefixed(level,source,line))
			elif self.DEBUG.LOG >=log.LOG_INFO:
				print self._prefixed(level,source,line)
				sys.stdout.flush()

	# notice

	def warning (self,message,source='',level='WARNING'):
		for line in message.split('\n'):
			if self._syslog:
				self._syslog.warning(self._prefixed(level,source,line))
			elif self.DEBUG.LOG >=log.LOG_WARNING:
				print self._prefixed(level,source,line)
				sys.stdout.flush()

	def error (self,message,source='',level='ERROR'):
		for line in message.split('\n'):
			if self._syslog:
				self._syslog.error(self._prefixed(level,source,line))
			elif self.DEBUG.LOG >=log.LOG_ERR:
				print self._prefixed(level,source,line)
				sys.stdout.flush()

	def critical (self,message,source='',level='CRITICAL'):
		for line in message.split('\n'):
			if self._syslog:
				self._syslog.critical(self._prefixed(level,source,line))
			elif self.DEBUG.LOG >=log.LOG_CRIT:
				print self._prefixed(level,source,line)
				sys.stdout.flush()

	# alert
	# emmergency
	# nothing

	# show the exchange of message generated by the supervisor (^C and signal received)
	def supervisor (self,message):
		if self.DEBUG.SUPERVISOR:
			self.info(message,'supervisor')
		else:
			self._record(time.localtime(),'supervisor','info',message)

	# show the exchange of message generated by the daemon feature (change pid, fork, ...)
	def daemon (self,message):
		if self.DEBUG.DAEMON:
			self.info(message,'daemon')
		else:
			self._record(time.localtime(),'daemon','info',message)

	# show the exchange of message generated by the connection handling class
	def server (self,message):
		if self.DEBUG.SERVER:
			self.info(message,'server')
		else:
			self._record(time.localtime(),'server','info',message)

	# show the data send and received to our client
	def client (self,message):
		if self.DEBUG.CLIENT:
			self.info(message,'client')
		else:
			self._record(time.localtime(),'client','info',message)

	# show what is happening to the processes
	def manager (self,message):
		if self.DEBUG.MANAGER:
			self.info(message,'manager')
		else:
			self._record(time.localtime(),'manager','info',message)

	# show the state of each worker thread
	def worker (self,message,prefix='worker'):
		if self.DEBUG.WORKER:
			self.info(message,prefix)
		else:
			self._record(time.localtime(),prefix,'info',message)

	# show the state of each download thread
	def download (self,message):
		if self.DEBUG.DOWNLOAD:
			self.info(message,'download')
		else:
			self._record(time.localtime(),'download','info',message)

	# show the state of each http thread
	def http (self,message):
		if self.DEBUG.HTTP:
			self.info(message,'http')
		else:
			self._record(time.localtime(),'http','info',message)


def Logger ():
	if _Logger._instance:
		return _Logger._instance
	instance = _Logger()
	_Logger._instance = instance
	return instance

if __name__ == '__main__':
	logger = Logger()
	logger.wire('wire packet content')
	logger.message('message exchanged')
	logger.debug('debug test')
	
