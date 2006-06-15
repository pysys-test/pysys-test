#!/usr/bin/env python
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and any associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# The software is provided "as is", without warranty of any
# kind, express or implied, including but not limited to the
# warranties of merchantability, fitness for a particular purpose
# and noninfringement. In no event shall the authors or copyright
# holders be liable for any claim, damages or other liability,
# whether in an action of contract, tort or otherwise, arising from,
# out of or in connection with the software or the use or other
# dealings in the software.
 
import asyncore, smtpd, threading

from pysys.constants import *;


class SimpleSMTPServer(smtpd.SMTPServer): 
	def __init__(self, localaddr, remoteaddr, filename='smtpserver.out', logMails=TRUE):
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
		

	

