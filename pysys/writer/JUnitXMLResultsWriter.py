import os, sys, stat

from pysys.constants import *
from xml.dom.minidom import getDOMImplementation

class JUnitXMLResultsWriter:
	def __init__(self, logfile):
		self.cycle = -1
		self.reports = os.path.join(PROJECT.root, 'target','pysys-reports')

	def setup(self, **kwargs):		
		if os.path.exists(self.reports): self.purgeDirectory(self.reports, True)
		os.makedirs(self.reports)

	def cleanup(self, **kwargs):
		pass
			
	def processResult(self, testObj, **kwargs):
		if kwargs.has_key("cycle"): 
			if self.cycle != kwargs["cycle"]:
				self.cycle = kwargs["cycle"]
		
		impl = getDOMImplementation()		
		document = impl.createDocument(None, 'testsuite', None)		
		rootElement = document.documentElement
		attr1 = document.createAttribute('name')
		attr1.value = testObj.descriptor.id
		attr2 = document.createAttribute('tests')
		attr2.value='1'
		attr3 = document.createAttribute('failures')
		attr3.value = '%d'%(int)(testObj.getOutcome() in FAILS)	
		attr4 = document.createAttribute('skipped')	
		attr4.value = '%d'%(int)(testObj.getOutcome() == SKIPPED)		
		rootElement.setAttributeNode(attr1)
		rootElement.setAttributeNode(attr2)
		rootElement.setAttributeNode(attr3)
		rootElement.setAttributeNode(attr4)
		
		# add the testcase information
		testcase = document.createElement('testcase')
 		attr1 = document.createAttribute('classname')
		attr1.value = testObj.descriptor.classname
 		attr2 = document.createAttribute('name')
		attr2.value = testObj.descriptor.id		   	
		testcase.setAttributeNode(attr1)
		testcase.setAttributeNode(attr2)
		
		# add in failure information if the test has failed
		if (testObj.getOutcome() in FAILS):
			failure = document.createElement('failure')
			attr1 = document.createAttribute('message')
			attr1.value = LOOKUP[testObj.getOutcome()]
			failure.setAttributeNode(attr1)		
						
			stdout = document.createElement('system-out')
			fp = open(os.path.join(testObj.output, 'run.log'))
			stdout.appendChild(document.createTextNode(fp.read()))
			fp.close()
			
			testcase.appendChild(failure)
			testcase.appendChild(stdout)
		rootElement.appendChild(testcase)
		
		# write out the test result
		if self.cycle > 0:
			fp = open(os.path.join(self.reports,'TEST-%s.%s.xml'%(testObj.descriptor.id, self.cycle)), 'w')
		else:
			fp = open(os.path.join(self.reports,'TEST-%s.xml'%(testObj.descriptor.id)), 'w')
		fp.write(document.toprettyxml(indent='	'))
		fp.close()
		
	def purgeDirectory(self, dir, delTop=False):
		for file in os.listdir(dir):
		  	path = os.path.join(dir, file)
		  	if PLATFORM in ['sunos', 'linux']:
		  		mode = os.lstat(path)[stat.ST_MODE]
		  	else:
		  		mode = os.stat(path)[stat.ST_MODE]
		
			if stat.S_ISLNK(mode):
				os.unlink(path)
			if stat.S_ISREG(mode):
				os.remove(path)
			elif stat.S_ISDIR(mode):
			  	self.purgeDirectory(path, delTop=True)				 

		if delTop: os.rmdir(dir)
		