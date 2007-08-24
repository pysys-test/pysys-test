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

import distutils.sysconfig, sys, os

lib_dir = distutils.sysconfig.get_python_lib(plat_specific=1)

def install():
	try:
		# The file system directory that contains the directories for the common program groups that appear 
		# on the Start menu for all users. A typical path is C:\Documents and Settings\All Users\Start Menu\Programs. 
		# Valid only for Windows NT systems.
		fldr = get_special_folder_path("CSIDL_COMMON_PROGRAMS")
	except:
		# The file system directory that contains the user's program groups (which are themselves file system directories)
		# A typical path is C:\Documents and Settings\username\Start Menu\Programs.
		fldr = get_special_folder_path("CSIDL_PROGRAMS")

	# Create the PySys link in start menu -> programs
	directory = os.path.join(fldr, "PySys")
	if not os.path.isdir(directory): os.mkdir(directory)
	directory_created(directory)
	sys.stdout.write("Created and registered %s \n" % directory)
	
	# Create a shortcut to the documentation
	filename = os.path.join(directory, "PySys Epydoc Documentation.lnk")
	description = "Documentation for the PySys module"
	create_shortcut("%s/pysys-doc/index.html"%lib_dir, description, filename)
	file_created(filename)
	sys.stdout.write("Created and registered link to documentation\n")

	# Create a shortcut to the release notes
	filename = os.path.join(directory, "Release Notes.lnk")
	description = "Release Notes for the PySys module"
	create_shortcut("%s/pysys-release.txt"%lib_dir, description, filename)
	file_created(filename)
	sys.stdout.write("Created and registered link to release notes\n")

	

def printUsage():
	print "\nUsage: %s [option]" % os.path.basename(sys.argv[0])
	print "    where option is one of;"
	print " 	  -install		   perform the post install steps"
	print " 	  -remove		   perform the post uninstall steps"
	print ""
	sys.exit()


if __name__=='__main__':
	if len(sys.argv)==1:
		printUsage()
		sys.exit(1)

	arg_index = 1
	while arg_index < len(sys.argv):
		arg = sys.argv[arg_index]

		if arg == "-install":
			install()
		elif arg == "-remove":
			pass
		else:
			print "Unknown option:", arg
			sys.exit(0)
		arg_index += 1
