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

docfiles = ['pysys-doc/epydoc.css', 'pysys-doc/epydoc.js']
docfiles.extend(glob.glob('pysys-doc/*.html'))

setup(name='PySys',
		version=pysys.__version__,
		author=pysys.__author__,
		author_email=pysys.__author_email__,
		description='Python System Test Framework',
		url="http://sourceforge.net/projects/pysys",
		packages=['pysys', 'pysys.launcher',  'pysys.manual', 'pysys.process', 'pysys.process.plat-win32', 
		          'pysys.process.plat-unix', 'pysys.utils', 'pysys.writer', 'pysys.xml'],
		data_files=[('%s/pysys-doc' % get_site_packages_path(), docfiles)],
		scripts = ['pysys-dist/pysys_postinstall.py']
		)