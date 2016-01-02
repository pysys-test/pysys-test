#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2016  M.B.Grieve

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

# Contact: moraygrieve@users.sourceforge.net
 
import asyncore, smtpd, threading

from pysys.constants import *


class SimpleSMTPServer(smtpd.SMTPServer): 
	def __init__(self, localaddr, remoteaddr, filename='smtpserver.out', logMails=True):
		smtpd.SMTPServer.__init__(self, localaddr, remoteaddr)
		try:
			self.fp = open(filename, 'w')
			self.logMails = logMails
			self.count = 0
		except:
			pass

	def process_message(self, peer, mailfrom, rcpttos, data):
		self.count = self.count + 1
		if self.fp:
			self.fp.write("SimpleSMTPServer: Message count = %d\n" % self.count)
			if self.logMails: self.fp.write(data)
			self.fp.flush()


class SimpleSMTPServerRunner:
	def __init__(self):
		self.exit = 0

	def kickoff(self):
		while not self.exit:
			asyncore.loop(timeout=1.0, use_poll=False, count=1)

	def start(self):
		threading.Thread(target=self.kickoff).start()

	def stop(self):
		self.exit = 1
		

	

