# PySys System Test Framework, Copyright (C) 2006-2021 M.B. Grieve

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

"""
:meta private: Not part of the PySys API. 
"""

from __future__ import print_function
import os.path, stat, getopt, logging, traceback, sys
import json

from pysys import log

from pysys import __version__
from pysys.constants import *
from pysys.config.project import getProjectConfigTemplates, createProjectConfig
from pysys.exceptions import UserError


def makeProject(args):
	_PYSYS_SCRIPT_NAME = os.path.basename(sys.argv[0]) if '__main__' not in sys.argv[0] else 'pysys.py'
	templatelist = ', '.join(sorted(getProjectConfigTemplates().keys()))
	def printUsage():
		print("\nPySys System Test Framework (version %s): Project configuration file maker" % __version__) 
		print("")
		print("Usage: %s makeproject [option]* [--template=TEMPLATE]" % (_PYSYS_SCRIPT_NAME))
		print("")
		print("   where TEMPLATE can be: %s"%templatelist)
		print("")
		print("   and [option] includes:")
		print("       -h | --help                 print this message")
		print("       -d | --dir      STRING      root directory in which to create project configuration file")
		print("                                   (default is current working dir)")
		print("")
		print("Project configuration templates are stored in: %s"%os.path.normpath(os.path.dirname(getProjectConfigTemplates()['default'])))
		sys.exit()

	optionString = 'hd:'
	optionList = ['dir=', 'help', 'template=']
	
	try:
		optlist, arguments = getopt.gnu_getopt(args, optionString, optionList)
	except Exception:
		log.warning("Error parsing command line arguments: %s" % (sys.exc_info()[1]))
		sys.exit(1)

	dir = '.'
	tmpl = 'default'
	for option, value in optlist:
		if option in ["-h", "--help"]:
			printUsage()
			
		if option in ["--template"]:
			tmpl = value	

		elif option in ["-d", "--dir"]:
			dir = value
			
		else:
			print("Unknown option: %s"%option)
			sys.exit(1)

	if arguments:
		print("Unexpected argument '%s'; maybe you meant to use --template"%arguments[0])
		sys.exit(1)
	
	templates = getProjectConfigTemplates()
	if tmpl not in templates:
		print("Unknown template '%s', please specify one of the following: %s"%(tmpl, templatelist))
		sys.exit(1)
	if os.path.exists(dir):
		for f in os.listdir(dir):
			if f in DEFAULT_PROJECTFILE:
				print("Cannot create as project file already exists: %s"%os.path.normpath(dir+'/'+f))
				sys.exit(1)

	createProjectConfig(dir, templates[tmpl])
	print("Successfully created project configuration in root directory '%s'."%os.path.normpath(dir))
	print("Now change to that directory and use 'pysys make' to create your first testcase.")
