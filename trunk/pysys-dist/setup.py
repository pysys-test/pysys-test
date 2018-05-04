#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2013  M.B.Grieve

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

import pysys, glob, sys, os
import distutils.sysconfig
from distutils.core import setup

if sys.version_info >= (3,):
  from distutils.command.build_py import build_py_2to3 as build_py
else:
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
					  (get_site_packages_path(), ['pysys-dist/README.rst']),
					  ]
if IS_WINDOWS: data_files.append(('%s/pysys-doc' % get_site_packages_path(), glob.glob('pysys-doc/*.*')))
	
setup(cmdclass = {'build_py': build_py},
	  name='PySys',
	  version=pysys.__version__,
	  author=pysys.__author__,
	  author_email=pysys.__author_email__,
	  description='Python System Test Framework',
	  url="http://www.sourceforge.net/projects/pysys",
	  scripts = ['pysys-dist/scripts/pysys.py', 'pysys-dist/scripts/pysys_postinstall.py'] if IS_WINDOWS
	  	else ['pysys-dist/scripts/pysys.py'],
	  packages=['pysys', 'pysys.launcher',  'pysys.manual',
				'pysys.process', 'pysys.process.plat-win32', 
				'pysys.process.plat-unix', 'pysys.unit', 'pysys.utils',
				'pysys.writer', 'pysys.xml'],
	  data_files=data_files,
	)
	
# to run on windows use
# python c:\Python24\Scripts\epydoc.py --no-private --html -o pysys-doc pysys
# python.exe pysys-dist/setup.py bdist_wininst --install-script pysys_postinstall.py
# winzip32.exe -min -a -r -p dist\PySys-examples.X.Y.Z.zip pysys-examples

# to run on unix use
# /usr/local/bin/python2.4 setup.py sdist
