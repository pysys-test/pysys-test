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

import pysys, glob, sys, os
import distutils.sysconfig
from distutils.core import setup

lib_dir = distutils.sysconfig.get_python_lib(plat_specific=1)

def get_site_packages_path():
	if sys.platform.lower().startswith('win'):
		return os.path.join("Lib", "site-packages")
	else:
		return os.path.join("lib", "python%s" % sys.version[:3], "site-packages")

		
if sys.platform.lower().startswith('win'):
	setup(name='PySys',
		  version=pysys.__version__,
		  author=pysys.__author__,
		  author_email=pysys.__author_email__,
		  description='Python System Test Framework',
		  url="http://www.sourceforge.net/projects/pysys",
		  scripts = ['pysys-dist/scripts/pysys.py', 'pysys-dist/scripts/pysys_postinstall.py'],
		  packages=['pysys', 'pysys.launcher',  'pysys.manual',
					'pysys.process', 'pysys.process.plat-win32', 
					'pysys.process.plat-unix', 'pysys.utils',
					'pysys.writer', 'pysys.xml'],
		  data_files=[('%s/pysys-doc' % get_site_packages_path(), ['pysys-doc/epydoc.css', 'pysys-doc/index.html']),
		  			  ('%s/pysys-doc/private' % get_site_packages_path(), glob.glob('pysys-doc/private/*.*')),
		  			  ('%s/pysys-doc/public' % get_site_packages_path(), glob.glob('pysys-doc/public/*.*')),
					  (get_site_packages_path(), ['pysys-dist/pysys-release.txt'])]
		)
else:
	setup(name='PySys',
		  version=pysys.__version__,
		  author=pysys.__author__,
		  author_email=pysys.__author_email__,
		  description='Python System Test Framework',
		  url="http://www.sourceforge.net/projects/pysys",
		  scripts = ['pysys-dist/scripts/pysys.py'],
		  packages=['pysys', 'pysys.launcher',  'pysys.manual',
					'pysys.process', 'pysys.process.plat-win32', 
					'pysys.process.plat-unix', 'pysys.utils',
					'pysys.writer', 'pysys.xml']
		)

	
# to run on windows use
# python c:\Python24\Scripts\epydoc.py --html -o pysys-doc pysys
# python.exe pysys-dist/setup.py bdist_wininst --install-script pysys_postinstall.py
# winzip32.exe -min -a -r -p dist\PySys-examples.X.Y.Z.zip pysys-examples

# to run on unix use
# /usr/local/bin/python2.4 setup.py sdist
