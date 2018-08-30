#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2019  M.B.Grieve

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

import codecs, os, glob, sys

import pysys

import setuptools
print('using setuptools v%s'%setuptools.__version__)
from setuptools import setup

# Conditional dependencies were added before v37, so need that version when building from source. 
# (end-users should be using the wheel so won't be affected).
assert int(setuptools.__version__.split(".", 1)[0]) >= 37, 'Please upgrade setuptools and wheel to latest versions (pip install --upgrade setuptools wheel); current setuptools=%s'%setuptools.__version__

ROOTDIR = os.path.abspath(os.path.dirname(__file__))

# classifiers come from PyPi's official list https://pypi.org/classifiers/
PLATFORMS_CLASSIFIERS = [
	"Operating System :: Microsoft :: Windows",
	"Operating System :: POSIX :: SunOS/Solaris",
	"Operating System :: POSIX :: Linux",
	"Operating System :: OS Independent",
]
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
	"Topic :: Software Development :: Quality Assurance",
	"Topic :: Software Development :: Testing",
	"Topic :: Education :: Testing",
	"Intended Audience :: Developers",
	"Intended Audience :: Education",
	"Natural Language :: English",
]+PLATFORMS_CLASSIFIERS
KEYWORDS = ['testing', 'qa', 'system testing', 'integration testing', 'unit testing']

with codecs.open(ROOTDIR+'/README.rst', "rb", "ascii") as f:
	long_description = f.read()

with codecs.open(ROOTDIR+'/VERSION', "rb", "ascii") as f:
	versionFromFile = f.read()
	assert versionFromFile == pysys.__version__, '"%s" != "%s"'%(versionFromFile, pysys.__version__) # ensure consistent version

setup(
	name='PySys',
	description='Python System Test Framework',
	
	url="https://github.com/pysys-test/pysys-test",
	project_urls={ # see PEP-0459
		'Documentation': 'https://pysys-test.github.io/pysys-test',
		'Repository': 'https://github.com/pysys-test/pysys-test',
		'Tracker': 'https://github.com/pysys-test/pysys-test/issues',
		'Change Log': 'https://github.com/pysys-test/pysys-test/blob/master/CHANGELOG.rst',
		'Stackoverflow Tag': 'https://stackoverflow.com/tags/pysys', 
		'Download Samples': 'https://github.com/pysys-test/pysys-test/releases',
	},

	version=pysys.__version__,
	author=pysys.__author__, 
	author_email=pysys.__maintainer_email__,
	maintainer=pysys.__maintainer__,
	maintainer_email=pysys.__maintainer_email__, 
	license=pysys.__license__,
	keywords=KEYWORDS,
	classifiers=CLASSIFIERS,
	platforms=PLATFORMS_CLASSIFIERS,
	long_description=long_description,
	long_description_content_type='text/x-rst',

	python_requires=">=2.7, <4", # be flexible

	install_requires=["pywin32;sys_platform=='win32'"],
	extras_require={'console_color_windows': ["colorama;sys_platform=='win32'"]},

	scripts = ['scripts/pysys.py'],
	packages=['pysys', 'pysys.launcher',  'pysys.manual',
			'pysys.process', 'pysys.process.plat-win32', 
			'pysys.process.plat-unix', 'pysys.unit', 'pysys.utils',
			'pysys.writer', 'pysys.xml'],
	include_package_data=True,
	)
	