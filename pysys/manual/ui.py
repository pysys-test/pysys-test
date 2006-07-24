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
	def __init__(self, owner, filename, logname):
		self.owner = owner
		self.root = Tk()
		self.root.title("PySys Manual Tester - [%s]" % self.owner.descriptor.id)
		self.root.resizable(TRUE, TRUE)
		self.textFrame = Frame(self.root, relief=RAISED, borderwidth=1, padx=16, pady=10)
		self.filename = filename
		self.steps = self.parseInputXML(self.filename)
		self.numberOfSteps = len(self.steps)
		self.logname = logname
		self.logFd = open(self.logname, "w", 0)
		self.testFlag = -1
		self.resultDict = {}
		self.currentStep = -1
		self.stepLabel = None
		self.isRunning = 1


	def start(self):
		self.compileGUI()
		Scale()
		self.root.mainloop()
	

	def stop(self):
		try:
			if self.logFd is not None:
				self.logFd.close()
		except:
			pass
		self.isRunning = 0
		self.root.quit()


	def running(self):
		return self.isRunning


	def parseInputXML(self, input):
		parser = XMLManualTestParser(input)
		steps = parser.getSteps()
		parser.unlink()
		return steps
			

	def compileGUI(self):
		backFlag=NORMAL
		nextFlag=NORMAL
		compFlag=DISABLED
		
		#initiate the text frame
		if self.currentStep == -1:
			self.textFrameGUI(self.owner.descriptor.title,  self.owner.descriptor.purpose)
			self.radioFrameGUI(DISABLED)
		else:
			self.textFrameGUI("Step %d: %s" %(self.steps[self.currentStep].number, self.steps[self.currentStep].title), 
							 self.steps[self.currentStep].description)
			if self.steps[self.currentStep].validate=="true" or	self.steps[self.currentStep].validate=="TRUE":
				self.radioFrameGUI(NORMAL)
			else:
				self.radioFrameGUI(DISABLED)

		# compile the visibility of the buttons
		if self.currentStep == -1:
			backFlag=DISABLED
		if self.currentStep==self.numberOfSteps-1:
			nextFlag=DISABLED
			compFlag=NORMAL
			
		# initiate the button frame
		self.buttonFrameGUI(backFlag, nextFlag, compFlag)

		# update the frame
		self.textFrame.update()


	def textFrameGUI(self, labelText, description):
		if self.stepLabel is not None:
			self.stepLabel.grid_remove()
		self.stepLabel = Label(self.textFrame, text=labelText, font=("Verdana", 10, "bold"), pady=5, justify=LEFT, wraplength=450)
		self.stepLabel.grid(row=1, sticky=W)
		
		yscrollbar = Scrollbar(self.textFrame, orient=VERTICAL)
		yscrollbar.grid(row=5, column=1, sticky=W+N+S, ipady=90)
		xscrollbar = Scrollbar(self.textFrame, orient=HORIZONTAL)
		xscrollbar.grid(row=6, column=0, sticky=S+W+E, ipadx=90)		

		message=Text(self.textFrame, height=17, width=70, xscrollcommand=xscrollbar.set, yscrollcommand=yscrollbar.set, padx=15, pady=10, wrap=WORD)		 
		yscrollbar.config(command=message.yview)
		xscrollbar.config(command=message.xview)
		message.tag_config("f", font=("Helvetica", 10, "bold"))
		message.tag_config("a", relief=GROOVE)
		message.insert(INSERT, description, ("f","a"))
		message.config(state=DISABLED)
		message.grid(row=5, column=0)
 
		
	def radioFrameGUI(self,	rstate):
		v=IntVar()
		radioFrame=Frame(self.textFrame, relief=RIDGE, borderwidth=2)
		Radiobutton(radioFrame,	text="Pass", variable=v, font=("Verdana", 10,"bold"), value=1, state=rstate	,command=self.callBackPassRadio).grid(row=2,column=0)
		Radiobutton(radioFrame,	text="Fail", variable=v, font=("Verdana", 10,"bold"), value=2, state=rstate	,command=self.callBackFailRadio).grid(row=2,column=1)
		radioFrame.grid(row=7, sticky=NW, pady=5)
		self.textFrame.grid(row=1) 


	def buttonFrameGUI(self, backFlag, nextFlag, compFlag):
		buttonFrame=Frame(self.root, relief=GROOVE, borderwidth=0, highlightthickness=5)	

		quitButton = Button(buttonFrame, relief=RIDGE ,justify=LEFT	,text="Quit", borderwidth="1",command=self.quitCallBack,font=("verdana",	10,"bold"))
		mygrid=quitButton.grid(row=0, column=0, sticky=W, ipadx=13, ipady=3, padx=5, pady=5)

		quitButton = Button(buttonFrame, justify=LEFT, text="",	borderwidth="0")
		mygrid=quitButton.grid(row=0, column=1, padx=30, pady=5)
		
		backButton = Button(buttonFrame, relief=RIDGE, justify=RIGHT, text="< Back", command=self.backCallBack,	borderwidth="1",font=("Verdana", 10,"bold"), state=backFlag)
		backButton.grid(row=0,column=3, padx=10, pady=5 ,ipadx=13, ipady=3)
		
		nextButton = Button(buttonFrame, relief=RIDGE, justify=RIGHT, text="Next >", command=self.nextCallBack,	borderwidth="1", font=("Verdana", 10,"bold"), state=nextFlag)
		nextButton.grid(row=0, column=4, padx=10, pady=5, ipadx=13, ipady=3) 
		
		compButton = Button(buttonFrame, relief=RIDGE,justify=RIGHT, text="Complete", command=self.completeCallBack, borderwidth="1", font=("Verdana",	10,"bold"),	state=compFlag)
		compButton.grid(row=0, column=5, padx=10, pady=5, ipadx=10, ipady=3)
		
		buttonFrame.grid(row=9, sticky=N+W+E+S)


	#call back for radio Button	Pass
	def callBackPassRadio(self):
		self.testFlag=1


	#call back for radio Button	Fail
	def callBackFailRadio(self):
		self.testFlag=0

		
	# call back	for	complete button	click 
	def completeCallBack(self):
		if (self.steps[self.currentStep].validate=="true" or self.steps[self.currentStep].validate=="TRUE"):
			if self.testFlag==-1:
				tkMessageBox.showwarning("Warning", "Please select the step outcome before continuing ...", parent=self.root)
			else:
				self.storeResult()
				self.logResults()
				self.stop()
		else:
			self.logResults()
			self.stop()


	# call back for quit button click
	def quitCallBack(self):
		self.logResults()
		self.logFd.write("Application terminated from quit")
		self.owner.outcome.append(BLOCKED)
		self.stop()
	

	# call back	for	back button click
	def backCallBack(self):
		self.currentStep=self.currentStep-1
		self.compileGUI()
		self.storeResult()

	
	# call back for the next button click
	def nextCallBack(self):
		if self.currentStep == -1:
			self.currentStep=self.currentStep+1
			self.compileGUI()
			return 
			
		if self.steps[self.currentStep].validate=="true" or self.steps[self.currentStep].validate=="TRUE":
			if self.testFlag==-1:
				tkMessageBox.showwarning("Warning", "Please select the step outcome before continuing ...", parent=self.root)
			else:
				self.storeResult()
				self.currentStep=self.currentStep+1
				self.testFlag=-1
		else:
			self.currentStep=self.currentStep+1
		self.compileGUI()		 


	def logResults(self, logname=None):
		inKey=1
		if len(self.resultDict.keys()):
			self.logFd.write("Test Execution Status;\n")
			self.logFd.write("XML Feed : " + self.filename + "\n\n")

			for	key in self.resultDict.keys():
				if self.resultDict[key]:
					myStr="Verification Step %d (%s) : %6s" %(inKey, self.steps[key].title, "PASSED\n")
					self.owner.outcome.append(PASSED)
				else:
					myStr="Verification Step %d (%s) : %6s" %(inKey, self.steps[key].title, "FAILED\n")
					self.owner.outcome.append(FAILED)
				self.logFd.write(myStr)
				inKey=inKey+1

		 
	#store the result
	def	storeResult(self):
		self.resultDict[self.currentStep]=self.testFlag

