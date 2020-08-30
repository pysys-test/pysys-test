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
			return f.read()
	with codecs.open(ROOT_DIR+'/docs/TestDescriptors.rst', 'w', 'ascii') as rstout:
		rstout.write(readtmpl('docs/TestDescriptors.rst.tmpl')\
			.replace('@PYSYSTESTXML@', '\n  '+'\n  '.join(readtmpl('samples/cookbook/test/demo-tests/PySysTestDescriptorSample/pysystest.xml').split('\n')))\
			.replace('@PYSYSDIRCONFIGXML@', '\n  '+'\n  '.join(readtmpl('samples/cookbook/test/demo-tests/pysysdirconfig_sample/pysysdirconfig.xml').split('\n'))))

	with codecs.open(ROOT_DIR+'/docs/ProjectConfiguration.rst', 'w', 'ascii') as rstout:
		rstout.write(readtmpl('docs/ProjectConfiguration.rst.tmpl'))
		
		inXML = False
		proj = readtmpl('samples/cookbook/test/pysysproject.xml').replace('\r','')

		for item in re.split(r'^([ \t]*<!--.*?-->[^\n]*\n)', proj, flags=re.MULTILINE | re.DOTALL):
			if not item.strip(): continue
		
			if '<!--' in item and ('~~' in item or '`' in item):
				item = item.strip()[4:-3]
				if inXML: rstout.write('\n')
				inXML = False
				
				# insert the comment contents not as quoted XML but as rst source, so links and headings work
				rstout.write(inspect.cleandoc(item)+'\n')
				continue

			if not inXML: 
				rstout.write('\n.. code-block:: xml')
				if not item.startswith('\n'): rstout.write('\n')
				rstout.write('\n  ')
			
			inXML=True
			rstout.write('\n  '.join(item.split('\n')))

if __name__ == '__main__':
	prepareDocBuild()
