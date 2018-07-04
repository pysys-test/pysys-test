#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2018  M.B.Grieve

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

# Contact: moraygrieve@users.sourceforge.net

import codecs, os
import pysys, glob, sys
import distutils.sysconfig
from distutils.core import setup

from distutils.command.build_py import build_py

lib_dir = distutils.sysconfig.get_python_lib(plat_specific=1)

IS_WINDOWS = sys.platform.lower().startswith('win')

def get_site_packages_path():
	if IS_WINDOWS:
		return os.path.join("Lib", "site-packages")
	else:
		return os.path.join("lib", "python%s" % sys.version[:3], "site-packages")

data_files = [(get_site_packages_path(), ['pysys-dist/pysys-release.txt']),
					  (get_site_packages_path(), ['pysys-dist/pysys-licence.txt']),
					  (get_site_packages_path(), ['pysys-dist/pysys-log.xsl']),
					  (get_site_packages_path()+'/pysys', ['pysys-dist/README.rst']),
					  ]
if IS_WINDOWS: data_files.append(('%s/pysys-doc' % get_site_packages_path(), glob.glob('pysys-doc/*.*')))

# classifiers come from PyPi's official list https://pypi.org/classifiers/
CLASSIFIERS = [
	"License :: OSI Approved :: GNU Lesser General Public License v2 (LGPLv2)",
	"Development Status :: 5 - Production/Stable",
	"Intended Audience :: Developers",
	"Programming Language :: Python",
	"Programming Language :: Python :: 2",
	"Programming Language :: Python :: 2.7",
	"Programming Language :: Python :: 3",
	"Programming Language :: Python :: 3.5",
	"Programming Language :: Python :: 3.6", 
	"Programming Language :: Python :: 3.7", # see also python_requires
	"Programming Language :: Python :: Implementation :: CPython",
	"Environment :: Console",
	"Operating System :: Microsoft :: Windows",
	"Operating System :: POSIX :: SunOS/Solaris",
	"Operating System :: POSIX :: Linux",
	"Topic :: Software Development :: Quality Assurance",
	"Topic :: Software Development :: Testing",
	"Topic :: Education :: Testing",
	"Intended Audience :: Developers",
	"Intended Audience :: Education",
	"Natural Language :: English",
]
KEYWORDS = ['testing', 'qa', 'system testing', 'integration testing', 'unit testing']

with codecs.open(os.path.abspath(os.path.dirname(__file__))+'/pysys-dist/README.rst', "rb", "ascii") as f:
	long_description = f.read()

setup(cmdclass = {'build_py': build_py},
	  name='PySys',
	  description='Python System Test Framework',
	  url="http://www.sourceforge.net/projects/pysys",
	  version=pysys.__version__,
	  author=pysys.__author__,
	  maintainer=pysys.__author__,
	  license=pysys.__license__,
	  author_email=pysys.__author_email__,
	  keywords=KEYWORDS,
	  classifiers=CLASSIFIERS,
	  long_description=long_description,
	  long_description_content_type='text/x-rst',
	  python_requires=">=2.7, <4", # be flexible
	  scripts = ['pysys-dist/scripts/pysys.py', 'pysys-dist/scripts/pysys_postinstall.py'] if IS_WINDOWS
	  	else ['pysys-dist/scripts/pysys.py'],
	  packages=['pysys', 'pysys.launcher',  'pysys.manual',
				'pysys.process', 'pysys.process.plat-win32', 
				'pysys.process.plat-unix', 'pysys.unit', 'pysys.utils',
				'pysys.writer', 'pysys.xml'],
	  data_files=data_files,
	)
	
