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
# dealings in the software

try:
	import tkMessageBox
	from Tkinter import *
except:
	pass

import logging
from pysys.constants import *
from pysys.exceptions import *
from pysys.xml.manual import XMLManualTestParser

log = logging.getLogger('pysys.manual.ui')
log.setLevel(logging.NOTSET)


class ManualTester:
	def __init__(self, owner, filename, logname=None):
		self.owner = owner
		self.parentContainer = Tk()
		self.parentContainer.protocol('WM_DELETE_WINDOW', self.quitPressed)
		self.parentContainer.wm_geometry("500x400")
		self.parentContainer.title("PySys Manual Tester - [%s]" % self.owner.descriptor.id)
		self.parentContainer.resizable(TRUE, TRUE)
		self.titleBox = Label(self.parentContainer, text="Test Title Here", font=("Verdana 10 bold"), padx=8, anchor=W, wraplength=480)
		self.titleBox.pack(fill=X, padx=5, pady=5)
		self.displayContainer = Frame(self.parentContainer)
		self.xscrollbar = Scrollbar(self.displayContainer, orient=HORIZONTAL)
		self.xscrollbar.pack(fill=X, side=BOTTOM)
		self.messageBox = Text(self.displayContainer, wrap=WORD, width=1, height=1, padx=10, pady=10)
		self.messageBox.insert(INSERT, "Test Body Here")
		self.messageBox.pack(fill=BOTH, expand=YES, side=LEFT)
		self.yscrollbar = Scrollbar(self.displayContainer, orient=VERTICAL)
		self.yscrollbar.pack(fill=Y, side=LEFT)
		self.yscrollbar.config(command=self.messageBox.yview)
		self.xscrollbar.config(command=self.messageBox.xview)
		self.displayContainer.pack(fill=BOTH, expand=YES, padx=5, pady=5)
		self.messageBox.config(xscrollcommand=self.xscrollbar.set, yscrollcommand=self.yscrollbar.set, font=("Helvetica 10"))
		separator = Frame(height=2, bd=1, relief=SUNKEN)
		separator.pack(fill=X, pady=2)
		self.inputContainer = Frame(self.parentContainer, relief=GROOVE)
		self.quitButton = Button(self.inputContainer, text="Quit", command=self.quitPressed, pady=5, padx=5, font=("Verdana 10 bold"))
		self.quitButton.pack(side=LEFT, padx=5, pady=5)
		self.backButton = Button(self.inputContainer, text="< Back", command=self.backPressed, state=DISABLED, pady=5, padx=5, font=("Verdana 10 bold"))
		self.backButton.pack(side=LEFT, padx=5, pady=5)
		self.multiButton = Button(self.inputContainer, text="Start", command=self.multiPressed, default=ACTIVE, pady=5, padx=5, font=("Verdana 10 bold"))
		self.multiButton.pack(side=RIGHT, padx=5, pady=5)
		self.failButton = Button(self.inputContainer, text="Fail", command=self.failPressed, pady=5, padx=5, font=("Verdana 10 bold"))
		self.failButton.pack(side=RIGHT, padx=5, pady=5)
		self.inputContainer.pack(fill=X, padx=5, pady=5)

		self.isRunning = 1
		self.filename = filename
		self.steps = self.parseInputXML(self.filename)
		self.currentStep = -1
		self.results = range(len(self.steps))
		self.doStep()

	def quitPressed(self):
		self.owner.log.critical("Application terminated by user (FAILED)")
		self.owner.outcome.append(FAILED)
		self.stop()

	def backPressed(self):
		if self.currentStep >= 0:
			self.currentStep = self.currentStep - 1
			self.doStep()

	def failPressed(self):
		self.results[self.currentStep] = 0
		self.currentStep = self.currentStep + 1
		self.doStep()

	def multiPressed(self):
		if self.currentStep == len(self.steps):
			self.stop()
			return
		elif self.currentStep >= 0:
			if self.steps[self.currentStep].validate == 'true':
				self.results[self.currentStep] = 1
			else: self.results[self.currentStep] = 2
		self.currentStep = self.currentStep + 1
		self.doStep()

	def doStep(self):
		self.messageBox.config(state=NORMAL, wrap=WORD)
		self.messageBox.delete(1.0, END)
		if self.currentStep < 0:
			self.multiButton.config(text="Start")
			self.backButton.config(state=DISABLED)
			self.failButton.forget()
			self.messageBox.insert(INSERT, self.owner.descriptor.purpose)
			self.titleBox.config(text="Title - %s" % self.owner.descriptor.title)
		elif self.currentStep == len(self.steps):
			self.multiButton.config(text="Finish")
			self.failButton.forget()
			self.messageBox.insert(INSERT, self.reportToString())
			self.titleBox.config(text="Test Complete - Summary Report")
		elif self.currentStep >= 0:
			if self.steps[self.currentStep].wrap == 'false':  self.messageBox.config(wrap=NONE)
			self.backButton.config(state=NORMAL)
			self.failButton.pack(side=RIGHT, padx=5, pady=5)
			self.multiButton.config(text="Pass")
			self.messageBox.insert(INSERT, self.steps[self.currentStep].description)
			self.titleBox.config(text="Step %s of %s - %s" % (self.currentStep + 1, len(self.steps), self.steps[self.currentStep].title))
			if self.steps[self.currentStep].validate == 'false':
				self.multiButton.config(text="Next >")
				self.failButton.forget()
		self.messageBox.config(state=DISABLED)

	def reportToString(self):
		result = ""
		intToRes = ["FAILED", "PASSED", "N/A"]
		for r in range(len(self.results)):
			result += "\nStep %s - %s: %s" % (r + 1, self.steps[r].title, intToRes[self.results[r]])
		return result

	def logResults(self):
		intToRes = ["FAILED", "PASSED", "N/A"]
		for r in range(len(self.results)):
			if r < self.currentStep:
				self.owner.log.info("Step %s - %s: %s" % (r + 1, self.steps[r].title, intToRes[self.results[r]]))
				if self.results[r] == 0: self.owner.outcome.append(FAILED)
				elif self.results[r] == 1: self.owner.outcome.append(PASSED)

	def start(self):
		self.parentContainer.mainloop()

	def stop(self):
		self.logResults()
		self.isRunning = 0
		self.parentContainer.quit()
		self.parentContainer.destroy()

	def running(self):
		return self.isRunning

	def parseInputXML(self, input):
		parser = XMLManualTestParser(input)
		steps = parser.getSteps()
		parser.unlink()
		return steps
