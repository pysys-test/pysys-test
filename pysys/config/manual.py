#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2021 M.B. Grieve

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

"""
Manual test loading.

:meta private: Really just used by the manual tester UI so not public API for now. 
"""

from __future__ import print_function
import os.path, logging, xml.dom.minidom

from pysys.constants import *

log = logging.getLogger('pysys.config.manual')

DTD='''
<!ELEMENT pysysmanualtest (step)+ >
<!ELEMENT step (description, expectedresult?) >
<!ELEMENT description (#PCDATA) >
<!ELEMENT expectedresult (#PCDATA) >
<!ATTLIST step title CDATA #REQUIRED
               validate (true | false) "true">
'''


class XMLManualTestStep(object): # pragma: no cover
	def __init__(self, number, title, validate, wrap, description, expectedResult):
		self.number = number
		self.title = title
		self.validate = validate
		self.wrap = wrap
		self.description = description
		self.expectedResult = expectedResult

		
	def toString(self):
		print("Step number:       %d" % self.number)
		print("Step title:        %s" % self.title) 
		print("Step validate:     %s" % self.validate)
		print("Step wrap:         %s" % self.wrap)
		sys.stdout.write("Step description:     ")
		desc = self.description.split('\n')
		for index in range(0, len(desc)):
			if index == 0: print(desc[index])
			if index != 0: print("                   %s" % desc[index])
		print("Expected result:   %s" % self.expectedResult)

class XMLManualTestParser(object): # pragma: no cover
	def __init__(self, xmlfile):
		self.dirname = os.path.dirname(xmlfile)
		self.xmlfile = xmlfile

		if not os.path.exists(xmlfile):
			raise Exception("Unable to find supplied manual test input file \"%s\"" % xmlfile)
		
		try:
			self.doc = xml.dom.minidom.parse(xmlfile)
		except Exception:
			raise Exception("%s " % (sys.exc_info()[1]))
		else:
			if self.doc.getElementsByTagName('pysysmanualtest') == []:
				raise Exception("No <pysysmanualtest> element supplied in XML descriptor")
			else:
				self.root = self.doc.getElementsByTagName('pysysmanualtest')[0]

				
	def unlink(self):
		if self.doc: self.doc.unlink()	

		
	def getSteps(self):
		stepsNodeList = self.root.getElementsByTagName('step')
		if stepsNodeList == []:
			raise Exception("No <step> element supplied in XML manual test input file")

		steps = []
		stepnumber = 0
		for stepsNode in stepsNodeList:
			title = stepsNode.getAttribute("title")
			validate = stepsNode.getAttribute("validate")
			wrap = stepsNode.getAttribute("wrap")

			if stepsNode.getElementsByTagName('description') == []:
				raise Exception("No <description> child element of <step> supplied in XML manual test input file")
			else:
				try:
					description = stepsNode.getElementsByTagName('description')[0].childNodes[0].data
				except Exception:
					description = ""
			try:
				expectedResult = stepsNode.getElementsByTagName('expectedresult')[0].childNodes[0].data
			except Exception:
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
