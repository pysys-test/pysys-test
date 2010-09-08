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

import os, os.path, sys, logging, xml.dom.minidom

from pysys.constants import *

log = logging.getLogger('pysys.xml.manual')

DTD='''
<!ELEMENT pysysmanualtest (step)+ >
<!ELEMENT step (description, expectedresult?) >
<!ELEMENT description (#PCDATA) >
<!ELEMENT expectedresult (#PCDATA) >
<!ATTLIST step title CDATA #REQUIRED
               validate (true | false) "true">
'''


class XMLManualTestStep:
	def __init__(self, number, title, validate, wrap, description, expectedResult):
		self.number = number
		self.title = title
		self.validate = validate
		self.wrap = wrap
		self.description = description
		self.expectedResult = expectedResult

		
	def toString(self):
		print "Step number:       %d" % self.number
		print "Step title:        %s" % self.title 
		print "Step validate:     %s" % self.validate
		print "Step wrap:         %s" % self.wrap
		print "Step description:     ",
		desc = self.description.split('\n')
		for index in range(0, len(desc)):
			if index == 0: print desc[index]
			if index != 0: print "                   %s" % desc[index]
		print "Expected result:   %s" % self.expectedResult

class XMLManualTestParser:
	def __init__(self, xmlfile):
		self.dirname = os.path.dirname(xmlfile)
		self.xmlfile = xmlfile

		if not os.path.exists(xmlfile):
			raise Exception, "Unable to find supplied manual test input file \"%s\"" % xmlfile
		
		try:
			self.doc = xml.dom.minidom.parse(xmlfile)
		except:
			raise Exception, "%s " % (sys.exc_info()[1])
		else:
			if self.doc.getElementsByTagName('pysysmanualtest') == []:
				raise Exception, "No <pysysmanualtest> element supplied in XML descriptor"
			else:
				self.root = self.doc.getElementsByTagName('pysysmanualtest')[0]

				
	def unlink(self):
		if self.doc: self.doc.unlink()	

		
	def getSteps(self):
		stepsNodeList = self.root.getElementsByTagName('step')
		if stepsNodeList == []:
			raise Exception, "No <step> element supplied in XML manual test input file"

		steps = []
		stepnumber = 0
		for stepsNode in stepsNodeList:
			title = stepsNode.getAttribute("title")
			validate = stepsNode.getAttribute("validate")
			wrap = stepsNode.getAttribute("wrap")

			if stepsNode.getElementsByTagName('description') == []:
				raise Exception, "No <description> child element of <step> supplied in XML manual test input file"
			else:
				try:
					description = stepsNode.getElementsByTagName('description')[0].childNodes[0].data
				except:
					description = ""
			try:
				expectedResult = stepsNode.getElementsByTagName('expectedresult')[0].childNodes[0].data
			except:
				expectedResult = ""
			stepnumber = stepnumber + 1
			steps.append(XMLManualTestStep(stepnumber, title, validate, wrap, description, expectedResult))
		return steps

	def putSteps(self, steps):
		stepsNodeList = self.root.getElementsByTagName('step')
		for step in stepsNodeList:
			self.root.removeChild(step)
			step.unlink()

		stepsNodeList = []

		for step in range(len(steps)):
			newStep = self.doc.createElement('step')
			newDesc = self.doc.createElement('description')
			newDesc.appendChild(self.doc.createCDATASection(""))
			newStep.appendChild(newDesc)
			newExp = self.doc.createElement('expectedresult')
			newExp.appendChild(self.doc.createCDATASection(""))
			newStep.appendChild(newExp)
			self.root.appendChild(newStep)
			stepsNodeList.append(newStep)

			if steps[step].expectedResult == "\n": steps[step].expectedResult = ""

			stepsNode = stepsNodeList[step]
			stepsNode.setAttribute("title", steps[step].title)
			stepsNode.setAttribute("validate", steps[step].validate)
			stepsNode.setAttribute("wrap", steps[step].validate)
			stepsNode.getElementsByTagName('description')[0].childNodes[0].data = steps[step].description
			stepsNode.getElementsByTagName('expectedresult')[0].childNodes[0].data = steps[step].expectedResult

	def writeXml(self):
		f = open(self.xmlfile, 'w')
		f.write(self.doc.toxml())
		f.close()
