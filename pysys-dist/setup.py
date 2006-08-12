#!/usr/bin/env python

import pysys, glob, sys, os
import distutils.sysconfig
from distutils.core import setup

lib_dir = distutils.sysconfig.get_python_lib(plat_specific=1)

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
		data_files=[('%s/pysys-doc' % lib_dir, docfiles)],
		scripts = ['pysys-dist/pysys_postinstall.py']
		)