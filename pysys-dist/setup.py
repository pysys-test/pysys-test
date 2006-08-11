#!/usr/bin/env python

import pysys, glob, sys, os
from distutils.core import setup

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
		data_files=[('%s/pysys-doc' % get_site_packages_path(), docfiles)]
		)