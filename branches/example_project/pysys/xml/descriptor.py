#!/usr/bin/env pytho
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

import os, os.path, sys, logging, xml.dom.minidom

from pysys.constants import *

log = logging.getLogger('pysys.xml.descriptor')

DTD='''
<!ELEMENT pysystest (description, classification?, data?, traceability?) > 
<!ELEMENT description (title, purpose) >
<!ELEMENT classification (groups?, modes?) >
<!ELEMENT data (class?, input?, output?, reference?) >
<!ELEMENT traceability (requirements) >
<!ELEMENT title (#PCDATA) >
<!ELEMENT purpose (#PCDATA) >
<!ELEMENT groups (group)+ >
<!ELEMENT modes (mode)+ >
<!ELEMENT class EMPTY >
<!ELEMENT input EMPTY >
<!ELEMENT output EMPTY >
<!ELEMENT reference EMPTY >
<!ELEMENT requirements (requirement)+ >  
<!ELEMENT group (#PCDATA) >
<!ELEMENT mode (#PCDATA) >
<!ELEMENT requirement EMPTY >
<!ATTLIST pysystest type (auto | manual ) "auto" >
<!ATTLIST pysystest state (runnable | deprecated | skipped) "runnable" >
<!ATTLIST class name CDATA #REQUIRED
                module CDATA #REQUIRED >
<!ATTLIST input path CDATA #REQUIRED >
<!ATTLIST output path CDATA #REQUIRED >
<!ATTLIST reference path CDATA #REQUIRED >
<!ATTLIST requirement id CDATA #REQUIRED >
'''


DESCRIPTOR_TEMPLATE ='''<?xml version="1.0" standalone="yes"?>
<pysystest type="%s" state="runnable">
    
  <description> 
    <title></title>    
    <purpose><![CDATA[
]]>
    </purpose>
  </description>

  <classification>
    <groups>
      <group>%s</group>
    </groups>
  </classification>

  <data>
    <class name="%s" module="%s"/>
  </data>
  
  <traceability>
    <requirements>
      <requirement id=""/>     
    </requirements>
  </traceability>
</pysystest>
''' 


class XMLDescriptorContainer:
	"""Holder class for the contents of a testcase descriptor. """

	def __init__(self, file, id, type, state, title, purpose, groups, modes, classname, module, input, output, reference, traceability):
		"""Create an instance of the XMLDescriptorContainer class.
		
		@param id: The testcase identifier
		@param type: The type of the testcase (automated or manual)
		@param state: The state of the testcase (runable, deprecated or skipped)
		@param title: The title of the testcase
		@param purpose: The purpose of the testcase
		@param groups: A list of the user defined groups the testcase belongs to
		@param modes: A list of the user defined modes the testcase can be run in
		@param classname: The classname of the testcase
		@param module: The full path to the python module containing the testcase class
		@param input: The full path to the input directory of the testcase
		@param output: The full path to the output parent directory of the testcase
		@param reference: The full path to the reference directory of the testcase
		@param traceability: A list of the requirements covered by the testcase
		
		"""
		self.file = file
		self.id = id
		self.type = type
		self.state = state
		self.title = title
		self.purpose = purpose
		self.groups = groups
		self.modes = modes
		self.classname = classname
		self.module = module
		self.input = input
		self.output = output
		self.reference = reference
		self.traceability = traceability

		
	def __str__(self):
		"""Return an informal string representation of the xml descriptor container object
		
		@return: The string represention
		@rtype: string
		"""
		
		str=    "Test id:           %s\n" % self.id
		str=str+"Test type:         %s\n" % self.type
		str=str+"Test state:        %s\n" % self.state
		str=str+"Test title:        %s\n" % self.title
		str=str+"Test purpose:      "
		purpose = self.purpose.split('\n')
		for index in range(0, len(purpose)):
			if index == 0: str=str+"%s\n" % purpose[index]
			if index != 0: str=str+"                   %s\n" % purpose[index] 
		str=str+"Test groups:       %s\n" % self.groups
		str=str+"Test modes:        %s\n" % self.modes
		str=str+"Test classname:    %s\n" % self.classname
		str=str+"Test module:       %s\n" % self.module
		str=str+"Test input:        %s\n" % self.input
		str=str+"Test output:       %s\n" % self.output
		str=str+"Test reference:    %s\n" % self.reference
		str=str+"Test traceability: %s\n" % self.traceability
		str=str+""
		return str


class XMLDescriptorCreator:
	'''Helper class to create a test descriptor template.'''
		
	def __init__(self, file, type="auto", group=DEFAULT_GROUP, testclass=DEFAULT_TESTCLASS, module=DEFAULT_MODULE):
		'''Class constructor.'''
		self.file=file
		self.type = type
		self.group = group
		self.testclass = testclass
		self.module = module
	
	def writeXML(self):
		'''Write a test descriptor template to file.'''
		fp = open(self.file, 'w')
		fp.writelines(DESCRIPTOR_TEMPLATE % (self.type, self.group, self.testclass, self.module))
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
		self.file = xmlfile
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
		return XMLDescriptorContainer(self.getFile(), self.getID(), self.getType(), self.getState(),
										self.getTitle(), self.getPurpose(),
										self.getGroups(), self.getModes(),
										self.getClassDetails()[0],
										os.path.join(self.dirname, self.getClassDetails()[1]),
										os.path.join(self.dirname, self.getTestInput()),
										os.path.join(self.dirname, self.getTestOutput()),
										os.path.join(self.dirname, self.getTestReference()),
										self.getRequirements())


	def unlink(self):
		'''Clean up the DOM on completion.'''
		if self.doc: self.doc.unlink()

	
	def getFile(self):
		'''Return the filename of the test descriptor.'''
		return self.file

	
	def getID(self):
		'''Return the id of the test.'''
		return os.path.basename(self.dirname)


	def getType(self):
		'''Return the type attribute of the test element.'''
		type = self.root.getAttribute("type")	
		if type == "":
			type = "auto"
		elif type not in ["auto", "manual"]:
			raise Exception, "The type attribute of the test element should be \"auto\" or \"manual\""
		return type


	def getState(self):
		'''Return the state attribute of the test element.'''
		state = self.root.getAttribute("state")	
		if state == "":
			state = "runnable"
		elif state not in ["runnable", "deprecated", "skipped"]: 
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
			
				
	def getGroups(self):
		'''Return a list of the group names, contained in the character data of the group elements.'''
		classificationNodeList = self.root.getElementsByTagName('classification')
		if classificationNodeList == []:
			raise Exception, "No <classification> element supplied in XML descriptor"
		
		groupList = []
		try:
			groups = classificationNodeList[0].getElementsByTagName('groups')[0]
			for node in groups.getElementsByTagName('group'):
				groupList.append(node.childNodes[0].data)
			return groupList
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
		print parser.getContainer()
		parser.unlink()

	elif sys.argv[1] == "create":
		creator = XMLDescriptorCreator(sys.argv[2])
		creator.writeXML()
		
	elif sys.argv[1] == "validate":
		from xml.parsers.xmlproc.xmlval import XMLValidator
		XMLValidator().parse_resource(sys.argv[2])
		
