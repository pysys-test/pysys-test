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

import os, os.path, sys, string, logging, xml.dom.minidom

from pysys.constants import *

log = logging.getLogger('pysys.xml.project')

DTD='''
<!ELEMENT pysysproject (property)+ >
<!ATTLIST property name CDATA #IMPLIED
                   value CDATA #IMPLIED
                   default CDATA #IMPLIED>
'''

EXPR1 = re.compile("^.*\${env.(?P<key>.*)}.*$")
EXPR2 = re.compile("^.*\${(?P<key>.*)}.*$")

class XMLProjectParser:
	def __init__(self, xmlfile):
		self.dirname = os.path.dirname(xmlfile)
		self.xmlfile = xmlfile
		self.properties = {}
		
		if not os.path.exists(xmlfile):
			raise Exception, "Unable to find supplied project file \"%s\"" % xmlfile
		
		try:
			self.doc = xml.dom.minidom.parse(xmlfile)
		except:
			raise Exception, "Error parsing supplied project file, " % (sys.exc_info()[1])
		else:
			if self.doc.getElementsByTagName('pysysproject') == []:
				raise Exception, "No <pysysproject> element supplied in project file"
			else:
			
				self.root = self.doc.getElementsByTagName('pysysproject')[0]

				
	def unlink(self):
		if self.doc: self.doc.unlink()	

		
	def getProperties(self):
		propertyNodeList = self.root.getElementsByTagName('property')

		for propertyNode in propertyNodeList:
			try:
				name = propertyNode.getAttribute("name") 
				value = propertyNode.getAttribute("value")
				
				if EXPR1.search(value) != None:
					key = re.match(EXPR1, value).group("key")
					try:
						insert = os.environ[key]
					except:
						insert = propertyNode.getAttribute("default")
					value = string.replace(value, r"${env.%s}"%key, insert)
				
				elif EXPR2.search(value) != None:
					key = re.match(EXPR2, value).group("key")
					try:
						insert = self.properties[re.match(EXPR2, value).group("key")]
					except :
						insert = propertyNode.getAttribute("default")
					value = string.replace(value, r"${%s}"%key, insert)
			except:
				pass
			else:
				self.properties[name] = value
		return self.properties


	def writeXml(self):
		f = open(self.xmlfile, 'w')
		f.write(self.doc.toxml())
		f.close()