#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2020  M.B.Grieve

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import codecs, os, glob, sys, shutil, re, inspect

import pysys
ROOT_DIR = os.path.normpath(os.path.dirname(__file__)+'/..')

# In the absence of cross-platform symlink support in git and to avoid duplicating it, create this on the fly
def prepareDocBuild():
	print('Creating dynamically-generated PySys .rst files')
	def readtmpl(path):
		with codecs.open(ROOT_DIR+'/'+path, 'r', 'ascii') as f:
			return f.read().replace('\r', '')


	def xmlToRST(xml):
			out = ''
			
			inXML = False
			proj = xml

			for item in re.split(r'^([ \t]*<!--.*?-->[^\n]*\n)', proj, flags=re.MULTILINE | re.DOTALL):
				if not item.strip(): continue
			
				if '<!--' in item and ('~~' in item or '`' in item):
					item = item.strip()[4:-3]
					if inXML: out += '\n'
					inXML = False
					
					# insert the comment contents not as quoted XML but as rst source, so links and headings work
					out += inspect.cleandoc(item)+'\n'
					continue

				if not inXML: 
					out += '\n.. code-block:: xml'
					if not item.startswith('\n'): out += '\n'
					out += '\n  '
				
				inXML=True
				out += '\n  '.join(item.split('\n'))
			return out
			
	with codecs.open(ROOT_DIR+'/docs/pysys/TestDescriptors.rst', 'w', 'ascii') as rstout:
		rstout.write(readtmpl('docs/pysys/TestDescriptors.rst.tmpl')\
			.replace('@PYSYSTESTXML@', '\n  '+'\n  '.join(readtmpl('samples/cookbook/test/demo-tests/PySysTestXMLDescriptorSample/pysystest.xml').split('\n')))\
			.replace('@PYSYSTESTPYTHON@', '\n  '+'\n  '.join(readtmpl('samples/cookbook/test/demo-tests/PySysTestPythonDescriptorSample/pysystest.py').split('\n')))\
			.replace('@PYSYSDIRCONFIGXML@', xmlToRST(readtmpl('samples/cookbook/test/demo-tests/pysysdirconfig_sample/pysysdirconfig.xml')))
			)


	with codecs.open(ROOT_DIR+'/docs/pysys/ProjectConfiguration.rst', 'w', 'ascii') as rstout:
			rstout.write(readtmpl('docs/pysys/ProjectConfiguration.rst.tmpl'))
			rstout.write(xmlToRST(readtmpl('samples/cookbook/test/pysysproject.xml')))


if __name__ == '__main__':
	prepareDocBuild()
