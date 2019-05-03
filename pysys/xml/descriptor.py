#!/usr/bin/env pytho
# PySys System Test Framework, Copyright (C) 2006-2019 M.B. Grieve

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



from __future__ import print_function
import os.path, logging, xml.dom.minidom
import collections

from pysys.constants import *
from pysys.exceptions import UserError

log = logging.getLogger('pysys.xml.descriptor')

DTD='''
<!ELEMENT pysystest (description, classification?, skipped?, run-order-priority?, id-prefix?, data?, traceability?) > 
<!ELEMENT description (title, purpose) >
<!ELEMENT classification (groups?, modes?) >
<!ELEMENT data (class?, input?, output?, reference?) >
<!ELEMENT traceability (requirements) >
<!ELEMENT run-order-priority (#PCDATA) >
<!ELEMENT id-prefix (#PCDATA) >
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
<!ATTLIST skipped reason >
<!ATTLIST class name CDATA #REQUIRED
                module CDATA #REQUIRED >
<!ATTLIST input path CDATA #REQUIRED >
<!ATTLIST output path CDATA #REQUIRED >
<!ATTLIST reference path CDATA #REQUIRED >
<!ATTLIST requirement id CDATA #REQUIRED >
'''


DESCRIPTOR_TEMPLATE ='''<?xml version="1.0" encoding="utf-8"?>
<pysystest type="%s">
  
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

  <!-- <skipped reason=""/> -->

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


class XMLDescriptorContainer(object):
	"""Contains descriptor metadata about an individual testcase. 
	
	Also used for descriptors specifying defaults for a directory subtree 
	containing a related set of testcases. 
	
	@ivar id: The testcase identifier; has the value None if this is a 
	directory config descriptor rather than a testcase descriptor. 
	@ivar type: The type of the testcase (automated or manual)
	@ivar state: The state of the testcase (runnable, deprecated or skipped)
	@ivar skippedReason: If set to a non-empty string, indicates that this 
	testcase is skipped and provides the reason. If this is set then the test 
	is skipped regardless of the value of `state`. 
	@ivar title: The title of the testcase
	@ivar purpose: The purpose of the testcase
	@ivar groups: A list of the user defined groups the testcase belongs to
	@ivar modes: A list of the user defined modes the testcase can be run in
	@ivar classname: The classname of the testcase
	@ivar module: The full path to the python module containing the testcase class
	@ivar input: The full path to the input directory of the testcase
	@ivar output: The full path to the output parent directory of the testcase
	@ivar reference: The full path to the reference directory of the testcase
	@ivar traceability: A list of the requirements covered by the testcase
	@ivar runOrderPriority: A float priority value used to determine the 
	order in which testcases will be run; higher values are executed before 
	low values. The default is 0.0. 

	"""


	def __init__(self, file, id, type, state, title, purpose, groups, modes, classname, module, input, output, reference, traceability, runOrderPriority=0.0, skippedReason=None):
		"""Create an instance of the XMLDescriptorContainer class.
		
		"""
		if skippedReason: state = 'skipped'
		if state=='skipped' and not skippedReason: skippedReason = '<unknown skipped reason>'
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
		self.runOrderPriority = runOrderPriority
		self.skippedReason = skippedReason
	
	def toDict(self):
		"""Converts this descriptor to an (ordered) dict suitable for serialization."""
		d = collections.OrderedDict()
		d['id'] = self.id
		d['xmlDescriptor'] = self.file
		d['type'] = self.type
		d['state'] = self.state
		d['skippedReason'] = self.skippedReason
		d['title'] = self.title
		d['purpose'] = self.purpose
		d['groups'] = self.groups
		d['modes'] = self.modes
		d['requirements'] = self.traceability
		d['runOrderPriority'] = self.runOrderPriority
		d['classname'] = self.classname
		d['module'] = self.module
		d['input'] = self.input
		d['output'] = self.output
		d['reference'] = self.reference
		
		return d
		
	def __str__(self):
		"""Return an informal string representation of the xml descriptor container object
		
		@return: The string represention
		@rtype: string
		"""
		
		str=    "Test id:           %s\n" % self.id
		str=str+"Test type:         %s\n" % self.type
		str=str+"Test state:        %s\n" % self.state
		if self.skippedReason: str=str+"Test skip reason:  %s\n" % self.skippedReason
		str=str+"Test title:        %s\n" % self.title
		str=str+"Test purpose:      "
		purpose = self.purpose.split('\n') if self.purpose is not None else ['']
		for index in range(0, len(purpose)):
			if index == 0: str=str+"%s\n" % purpose[index]
			if index != 0: str=str+"                   %s\n" % purpose[index] 
		str=str+"Test run order:    %s%s\n" % ('+' if self.runOrderPriority>0.0 else '', self.runOrderPriority)
		str=str+"Test groups:       %s\n" % (u', '.join((u"'%s'"%x if u' ' in x else x) for x in self.groups) or u'<none>')
		str=str+"Test modes:        %s\n" % (u', '.join((u"'%s'"%x if u' ' in x else x) for x in self.modes) or u'<none>')
		str=str+"Test classname:    %s\n" % self.classname
		str=str+"Test module:       %s\n" % self.module
		str=str+"Test input:        %s\n" % self.input
		str=str+"Test output:       %s\n" % self.output
		str=str+"Test reference:    %s\n" % self.reference
		str=str+"Test traceability: %s\n" % (u', '.join((u"'%s'"%x if u' ' in x else x) for x in self.traceability) or u'<none>')
		str=str+""
		return str

class XMLDescriptorCreator(object):
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



class XMLDescriptorParser(object):
	'''Helper class to parse an XML test descriptor - either for a testcase, 
	or for defaults for a (sub-)directory of testcases.

	The class uses the minidom DOM (Document Object Model) non validating
	parser to provide accessor methods to return element attributes	and character
	data from the test descriptor file. The class is instantiated with the filename
	of the test descriptor. It is the responsibility of the user of the class to
	call the unlink() method of the class on completion in order to free the memory
	used in the parsing.
	
	'''

	def __init__(self, xmlfile, istest=True, parentDirDefaults=None):
		self.file = xmlfile
		self.dirname = os.path.dirname(xmlfile)
		self.istest = istest
		self.defaults = self.DEFAULT_DESCRIPTOR if parentDirDefaults is None else parentDirDefaults
		roottag = 'pysystest' if istest else 'pysysdirconfig'
		if not os.path.exists(xmlfile):
			raise UserError("Unable to find supplied descriptor \"%s\"" % xmlfile)
		
		try:
			self.doc = xml.dom.minidom.parse(xmlfile)
		except Exception as ex:
			raise UserError("Invalid XML in descriptor '%s': %s" % (xmlfile, ex))
		else:
			if self.doc.getElementsByTagName(roottag) == []:
				raise UserError("No <%s> element supplied in XML descriptor '%s'"%(roottag, xmlfile))
			else:
				self.root = self.doc.getElementsByTagName(roottag)[0]

	@staticmethod
	def parse(xmlfile, istest=True, parentDirDefaults=None):
		"""
		Parses the test/dir descriptor in the specified path and returns the 
		XMLDescriptorContainer object. 
		
		@param istest: True if this is a pysystest.xml file, false if it is 
		a descritor giving defaults for a directory of testcases.  
		@param parentDirDefaults: Optional XMLDescriptorContainer instance 
		specifying default values to be filtered in from the parent 
		directory.
		"""
		p = XMLDescriptorParser(xmlfile, istest=istest, parentDirDefaults=parentDirDefaults)
		try:
			return p.getContainer()
		finally:
			p.unlink()

	DEFAULT_DESCRIPTOR = XMLDescriptorContainer(
		file=None, id=u'', type="auto", state="runnable", 
		title='', purpose='', groups=[], modes=[], 
		classname=DEFAULT_TESTCLASS, module=DEFAULT_MODULE,
		input=DEFAULT_INPUT, output=DEFAULT_OUTPUT, reference=DEFAULT_REFERENCE, 
		traceability=[], runOrderPriority=0.0, skippedReason=None)
	"""
	A directory config descriptor instance of XMLDescriptorContainer holding 
	the default values to be used if there is no directory config descriptor. 
	"""


	def getContainer(self):
		'''Create and return an instance of XMLDescriptorContainer for the contents of the descriptor.'''
		
		for attrName, attrValue in self.root.attributes.items():
			if attrName not in ['state', 'type']:
				raise UserError('Unknown attribute "%s" in XML descriptor "%s"'%(attrName, self.file))
		
		# some elements that are mandatory for an individual test and not used for dir config
		return XMLDescriptorContainer(self.getFile(), self.getID(), self.getType(), self.getState(),
										self.getTitle() if self.istest else None, self.getPurpose() if self.istest else None,
										self.getGroups(), self.getModes(),
										self.getClassDetails()[0],
										# don't absolutize for dir config descriptors, since we don't yet know the test's dirname
										os.path.join(self.dirname if self.istest else '', self.getClassDetails()[1]),
										os.path.join(self.dirname if self.istest else '', self.getTestInput()),
										os.path.join(self.dirname if self.istest else '', self.getTestOutput()),
										os.path.join(self.dirname if self.istest else '', self.getTestReference()),
										self.getRequirements(), 
										self.getRunOrderPriority(), 
										skippedReason=self.getSkippedReason())


	def unlink(self):
		'''Clean up the DOM on completion.'''
		if self.doc: self.doc.unlink()

	
	def getFile(self):
		'''Return the filename of the test descriptor.'''
		return self.file

	
	def getID(self):
		'''Return the id of the test, or for a pysysdirconfig, the id prefix.'''
		id = self.defaults.id
		for e in self.root.getElementsByTagName('id-prefix'):
			id = id+self.getText(e)
		
		for c in u'\\/:~#<>':
			# reserve a few characters that we might need for other purposes; _ and . can be used however
			if c in id:
				raise UserError('The <id-prefix> is not permitted to contain "%s"; error in "%s"'%(c, self.file))
		
		if self.istest: id = id+os.path.basename(self.dirname)
		
		return id


	def getType(self):
		'''Return the type attribute of the test element.'''
		type = self.root.getAttribute("type") or self.defaults.type
		if type not in ["auto", "manual"]:
			raise UserError("The type attribute of the test element should be \"auto\" or \"manual\" in \"%s\""%self.file)
		return type


	def getState(self):
		'''Return the state attribute of the test element.'''
		state = self.root.getAttribute("state")	 or self.defaults.state
		if state not in ["runnable", "deprecated", "skipped"]: 
			raise UserError("The state attribute of the test element should be \"runnable\", \"deprecated\" or \"skipped\" in \"%s\""%self.file)
		return state 

	def getSkippedReason(self):
		for e in self.root.getElementsByTagName('skipped'):
			r = (e.getAttribute('reason') or '').strip() 
			# make this mandatory, to encourage good practice
			if not r: raise UserError('Missing reason= attribute in <skipped> element of "%s"'%self.file)
			return r
		return self.defaults.skippedReason

	def getTitle(self):
		'''Return the test titlecharacter data of the description element.'''
		descriptionNodeList = self.root.getElementsByTagName('description')
		if descriptionNodeList == []:
			raise UserError("No <description> element supplied in XML descriptor \"%s\""%self.file)
		
		if descriptionNodeList[0].getElementsByTagName('title') == []:
			raise UserError("No <title> child element of <description> supplied in XML descriptor \"%s\""%self.file)
		else:
			try:
				title = descriptionNodeList[0].getElementsByTagName('title')[0]
				return title.childNodes[0].data.strip()
			except Exception:
				return self.defaults.title
				
				
	def getPurpose(self):
		'''Return the test purpose character data of the description element.'''
		descriptionNodeList = self.root.getElementsByTagName('description')
		if descriptionNodeList == []:
			raise UserError("No <description> element supplied in XML descriptor \"%s\""%self.file)
		
		if descriptionNodeList[0].getElementsByTagName('purpose') == []:
			raise UserError("No <purpose> child element of <description> supplied in XML descriptor \"%s\""%self.file)
		else:
			try:
				purpose = descriptionNodeList[0].getElementsByTagName('purpose')[0]
				return purpose.childNodes[0].data.strip()
			except Exception:
				return self.defaults.purpose
			
				
	def getGroups(self):
		'''Return a list of the group names, contained in the character data of the group elements.'''
		classificationNodeList = self.root.getElementsByTagName('classification')
		groupList = []
		try:
			groups = classificationNodeList[0].getElementsByTagName('groups')[0]
			for node in groups.getElementsByTagName('group'):
				if self.getText(node): groupList.append(self.getText(node))
		except Exception:
			pass
		groupList = [x for x in self.defaults.groups if x not in groupList]+groupList
		return groupList
	
				
	def getModes(self):
		'''Return a list of the mode names, contained in the character data of the mode elements.'''
		classificationNodeList = self.root.getElementsByTagName('classification')
		
		modeList = []
		try:
			modes = classificationNodeList[0].getElementsByTagName('modes')[0]
			for node in modes.getElementsByTagName('mode'):
				if self.getText(node): modeList.append(self.getText(node))
		except Exception:
			pass
		modeList = [x for x in self.defaults.modes if x not in modeList]+modeList
		return modeList

				
	def getClassDetails(self):
		'''Return the test class attributes (name, module, searchpath), contained in the class element.'''
		try:
			dataNodeList = self.root.getElementsByTagName('data')
			el = dataNodeList[0].getElementsByTagName('class')[0]
			return [el.getAttribute('name'), el.getAttribute('module')]
		except Exception:
			return [self.defaults.classname, self.defaults.module]

	def getRunOrderPriority(self):
		r = None
		for e in self.root.getElementsByTagName('run-order-priority'):
			r = self.getText(e)
			if r:
				try:
					r = float(r)
				except Exception:
					raise UserError('Invalid float value specified for run-order-priority in "%s"'%self.file)
		if r is None or r == '': 
			return self.defaults.runOrderPriority
		else:
			return r
			
	def getTestInput(self):
		'''Return the test input path, contained in the input element.'''
		try:
			dataNodeList = self.root.getElementsByTagName('data')
			input = dataNodeList[0].getElementsByTagName('input')[0]
			return input.getAttribute('path')
		except Exception:
			return self.defaults.input

			
	def getTestOutput(self):
		'''Return the test output path, contained in the output element.'''
		try:
			dataNodeList = self.root.getElementsByTagName('data')
			output = dataNodeList[0].getElementsByTagName('output')[0]
			return output.getAttribute('path')
		except Exception:
			return self.defaults.output


	def getTestReference(self):
		'''Return the test reference path, contained in the reference element.'''
		try:
			dataNodeList = self.root.getElementsByTagName('data')
			ref = dataNodeList[0].getElementsByTagName('reference')[0]
			return ref.getAttribute('path')
		except Exception:
			return self.defaults.reference


	def getRequirements(self):
		'''Return a list of the requirement ids, contained in the character data of the requirement elements.'''
		reqList = []			
		try:
			traceabilityNodeList = self.root.getElementsByTagName('traceability')
			requirements = traceabilityNodeList[0].getElementsByTagName('requirements')[0]
			for node in requirements.getElementsByTagName('requirement'):
				if node.getAttribute('id'): reqList.append(node.getAttribute('id'))
		except Exception:
			pass
		reqList = [x for x in self.defaults.traceability if x not in reqList]+reqList
		return reqList

	@staticmethod
	def getText(element):
		"""Utility method that reads text from the specified element and 
		strips leading/trailing whitespace from it. Returns an empty string if none. """
		t = u''
		if not element: return t
		for n in element.childNodes:
			if (n.nodeType == element.TEXT_NODE) and n.data:
				t += n.data
		return t.strip()

# entry point when running the class from the command line
# (used for development, testing, demonstration etc)
if __name__ == "__main__":

	if ( len(sys.argv) < 2 ) or ( sys.argv[1] not in ("create", "parse", "validate") ):
		print("Usage: %s (create | parse ) filename" % os.path.basename(sys.argv[0]))
		sys.exit()
	
	if sys.argv[1] == "parse":
		parser = XMLDescriptorParser(sys.argv[2])
		print(parser.getContainer())
		parser.unlink()

	elif sys.argv[1] == "create":
		creator = XMLDescriptorCreator(sys.argv[2])
		creator.writeXML()
		
	elif sys.argv[1] == "validate":
		from xml.parsers.xmlproc.xmlval import XMLValidator
		XMLValidator().parse_resource(sys.argv[2])
		
