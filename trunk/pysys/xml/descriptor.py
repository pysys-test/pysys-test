#!/usr/bin/env pytho
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

log = logging.getLogger('pysys.xml.descriptor')

DTD='''
<!ELEMENT pysystest (description, classification?, data?, traceability?) > 
<!ELEMENT description (title, purpose) >
<!ELEMENT classification (suites?, modes?) >
<!ELEMENT data (class?, input?, output?, reference?) >
<!ELEMENT traceability (requirements) >
<!ELEMENT title (#PCDATA) >
<!ELEMENT purpose (#PCDATA) >
<!ELEMENT suites (suite)+ >
<!ELEMENT modes (mode)+ >
<!ELEMENT class EMPTY >
<!ELEMENT input EMPTY >
<!ELEMENT output EMPTY >
<!ELEMENT reference EMPTY >
<!ELEMENT requirements (requirement)+ >  
<!ELEMENT suite (#PCDATA) >
<!ELEMENT mode (#PCDATA) >
<!ELEMENT requirement EMPTY >
<!ATTLIST pysystest state (runnable | deprecated | skipped) "runnable" >
<!ATTLIST class name CDATA #REQUIRED
                module CDATA #REQUIRED >
<!ATTLIST input path CDATA #REQUIRED >
<!ATTLIST output path CDATA #REQUIRED >
<!ATTLIST reference path CDATA #REQUIRED >
<!ATTLIST requirement id CDATA #REQUIRED >
'''


TEMPLATE ='''<?xml version="1.0" standalone="yes"?>
<pysytest state="runnable">
    
  <description> 
    <title></title>    
    <purpose><![CDATA[
]]>
    </purpose>
  </description>

  <classification>
    <suites>
      <suite>%s</suite>
    </suites>
  </classification>

  <data>
    <class name="%s" module="%s"/>
  </data>
</pysystest>
''' 


class XMLDescriptorContainer:
	'''Holder class for the contents of a test descriptor.'''

	def __init__(self, id, state, title, purpose, suites, modes, classname, module, input, output, reference, traceability):
		'''Class constructor.'''
		self.id = id
		self.state = state
		self.title = title
		self.purpose = purpose
		self.suites = suites
		self.modes = modes
		self.classname = classname
		self.module = module
		self.input = input
		self.output = output
		self.reference = reference
		self.traceability = traceability

		
	def toString(self):
		print "Test id:           %s" % self.id
		print "Test state:        %s" % self.state
		print "Test title:        %s" % self.title
		print "Test purpose:     ",
		purpose = self.purpose.split('\n')
		for index in range(0, len(purpose)):
			if index == 0: print purpose[index]
			if index != 0: print "                   %s" % purpose[index] 
		print "Test suites:       %s" % self.suites
		print "Test modes:        %s" % self.modes
		print "Test classname:    %s" % self.classname
		print "Test module:       %s" % self.module
		print "Test input:        %s" % self.input
		print "Test output:       %s" % self.output
		print "Test reference:    %s" % self.reference
		print "Test traceability: %s" % self.traceability



class XMLDescriptorCreator:
	'''Helper class to create a test desriptor template.'''
		
	def __init__(self, file, suite=DEFAULT_SUITE, testclass=DEFAULT_TESTCLASS, module=DEFAULT_MODULE):
		'''Class constructor.'''
		self.file=file
		self.suite = suite
		self.testclass = testclass
		self.module = module
	
	def writeXML(self):
		'''Write a test descriptor template to file.'''
		fp = open(self.file, 'w')
		fp.writelines(TEMPLATE % (self.suite, self.testclass, self.module))
		fp.close



class XMLDescriptorParser:
	'''Helper class to parse an XML test descriptor.

	The class uses the minidom DOM (Document Object Model) non validating
	parser to provide accessor methods to return element attributes	and character
	data from the test descriptor file. The class is instantiated with the filename
	of the test descriptor. It is the responsibility of the user of the class to
	call the unlink() method of the class on completion in order to free the memory
	used in the parsing.
	
	'''

	def __init__(self, xmlfile):
		'''Class constructor.'''		
		self.dirname = os.path.dirname(xmlfile)
		if not os.path.exists(xmlfile):
			raise Exception, "Unable to find supplied test descriptor \"%s\"" % xmlfile
		
		try:
			self.doc = xml.dom.minidom.parse(xmlfile)
		except:
			raise Exception, "%s " % (sys.exc_info()[1])
		else:
			if self.doc.getElementsByTagName('pysystest') == []:
				raise Exception, "No <pysystest> element supplied in XML descriptor"
			else:
				self.root = self.doc.getElementsByTagName('pysystest')[0]


	def getContainer(self):
		'''Create and return an instance of XMLDescriptorContainer for the contents of the descriptor.'''
		return XMLDescriptorContainer(self.getID(), self.getState(),
										self.getTitle(), self.getPurpose(),
										self.getsuites(), self.getModes(),
										self.getClassDetails()[0],
										os.path.join(self.dirname, self.getClassDetails()[1]),
										os.path.join(self.dirname, self.getTestInput()),
										os.path.join(self.dirname, self.getTestOutput()),
										os.path.join(self.dirname, self.getTestReference()),
										self.getRequirements())


	def unlink(self):
		'''Clean up the DOM on completion.'''
		if self.doc: self.doc.unlink()

		
	def getID(self):
		'''Return the id of the test.'''
		return os.path.basename(self.dirname)
	
	
	def getState(self):
		'''Return the state attribute of the test element.'''
		state = self.root.getAttribute("state")	
		if state not in ["runnable", "deprecated", "skipped"]: 
			raise Exception, "The state attribute of the test element should be \"runnable\", \"deprecated\" or \"skipped\""
		return state 
	

	def getTitle(self):
		'''Return the test titlecharacter data of the description element.'''
		descriptionNodeList = self.root.getElementsByTagName('description')
		if descriptionNodeList == []:
			raise Exception, "No <description> element supplied in XML descriptor"
		
		if descriptionNodeList[0].getElementsByTagName('title') == []:
			raise Exception, "No <title> child element of <description> supplied in XML descriptor"
		else:
			try:
				title = descriptionNodeList[0].getElementsByTagName('title')[0]
				return title.childNodes[0].data
			except:
				return ""
				
				
	def getPurpose(self):
		'''Return the test purpose character data of the description element.'''
		descriptionNodeList = self.root.getElementsByTagName('description')
		if descriptionNodeList == []:
			raise Exception, "No <description> element supplied in XML descriptor"
		
		if descriptionNodeList[0].getElementsByTagName('purpose') == []:
			raise Exception, "No <purpose> child element of <description> supplied in XML descriptor"
		else:
			try:
				purpose = descriptionNodeList[0].getElementsByTagName('purpose')[0]
				return purpose.childNodes[0].data
			except:
				return ""
			
				
	def getsuites(self):
		'''Return a list of the suite names, contained in the character data of the suite elements.'''
		classificationNodeList = self.root.getElementsByTagName('classification')
		if classificationNodeList == []:
			raise Exception, "No <classification> element supplied in XML descriptor"
		
		suiteList = []
		try:
			suites = classificationNodeList[0].getElementsByTagName('suites')[0]
			for node in suites.getElementsByTagName('suite'):
				suiteList.append(node.childNodes[0].data)
			return suiteList
		except:
			return []
	
				
	def getModes(self):
		'''Return a list of the mode names, contained in the character data of the mode elements.'''
		classificationNodeList = self.root.getElementsByTagName('classification')
		if classificationNodeList == []:
			raise Exception, "No <classification> element supplied in XML descriptor"
		
		modeList = []
		try:
			modes = classificationNodeList[0].getElementsByTagName('modes')[0]
			for node in modes.getElementsByTagName('mode'):
				modeList.append(node.childNodes[0].data)
			return modeList
		except:
			return []

				
	def getClassDetails(self):
		'''Return the test class attributes (name, module, searchpath), contained in the class element.'''
		try:
			dataNodeList = self.root.getElementsByTagName('data')
			el = dataNodeList[0].getElementsByTagName('class')[0]
			return [el.getAttribute('name'), el.getAttribute('module')]
		except:
			return [DEFAULT_TESTCLASS, DEFAULT_MODULE]

			
	def getTestInput(self):
		'''Return the test input path, contained in the input element.'''
		try:
			dataNodeList = self.root.getElementsByTagName('data')
			input = dataNodeList[0].getElementsByTagName('input')[0]
			return input.getAttribute('path')
		except:
			return DEFAULT_INPUT

			
	def getTestOutput(self):
		'''Return the test output path, contained in the output element.'''
		try:
			dataNodeList = self.root.getElementsByTagName('data')
			output = dataNodeList[0].getElementsByTagName('output')[0]
			return output.getAttribute('path')
		except:
			return DEFAULT_OUTPUT


	def getTestReference(self):
		'''Return the test reference path, contained in the reference element.'''
		try:
			dataNodeList = self.root.getElementsByTagName('data')
			ref = dataNodeList[0].getElementsByTagName('reference')[0]
			return ref.getAttribute('path')
		except:
			return DEFAULT_REFERENCE


	def getRequirements(self):
		'''Return a list of the requirement ids, contained in the character data of the requirement elements.'''
		reqList = []			
		try:
			traceabilityNodeList = self.root.getElementsByTagName('traceability')
			requirements = traceabilityNodeList[0].getElementsByTagName('requirements')[0]
			for node in requirements.getElementsByTagName('requirement'):
				reqList.append(node.getAttribute('id'))
			return reqList
		except:
			return []
					

# entry point when running the class from the command line
# (used for development, testing, demonstration etc)
if __name__ == "__main__":

	if ( len(sys.argv) < 2 ) or ( sys.argv[1] not in ("create", "parse", "validate") ):
		print "Usage: %s (create | parse ) filename" % os.path.basename(sys.argv[0])
		sys.exit()
	
	if sys.argv[1] == "parse":
		parser = XMLDescriptorParser(sys.argv[2])
		parser.getContainer().toString()
		parser.unlink()

	elif sys.argv[1] == "create":
		creator = XMLDescriptorCreator(sys.argv[2])
		creator.writeXML()
		
	elif sys.argv[1] == "validate":
		from xml.parsers.xmlproc.xmlval import XMLValidator
		XMLValidator().parse_resource(sys.argv[2])
		