#!/usr/bin/env python

import pysys
from distutils.core import setup

setup(name='PySys',
		version=pysys.__version__,
		author=pysys.__author__,
		author_email=pysys.__author_email__,
		description='Python System Test Framework',
		url="http://sourceforge.net/projects/pysys",
		packages=['pysys', 'pysys.launcher',  'pysys.manual', 'pysys.process', 'pysys.process.plat-win32', 'pysys.process.plat-unix', 'pysys.utils', 'pysys.writer', 'pysys.xml']
		)
