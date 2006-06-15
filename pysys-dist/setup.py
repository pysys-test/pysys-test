#!/usr/bin/env python

from distutils.core import setup

setup(name='PySys',
		version='0.1.1',
		description='Python System Test Framework',
		author='Moray Grieve',
		author_email='moraygrieve@users.sourceforge.net',
		url="http://sourceforge.net/projects/pysys",
		packages=['pysys', 'pysys.launcher',  'pysys.manual', 'pysys.process', 'pysys.process.plat-win32', 'pysys.process.plat-unix', 'pysys.utils', 'pysys.xml']
		)
