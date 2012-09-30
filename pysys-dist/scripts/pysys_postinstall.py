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

python_dir = distutils.sysconfig.get_config_var("prefix")
python_lib_dir = distutils.sysconfig.get_python_lib(plat_specific=1)

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
	pysysDirectory = os.path.join(fldr, "PySys")
	if not os.path.isdir(pysysDirectory): os.mkdir(pysysDirectory)
	directory_created(pysysDirectory)
	sys.stdout.write("Created and registered %s \n" % pysysDirectory)
	
	# Create the extensions directory link in start menu -> programs -> PySys
	extensionsDirectory = os.path.join(pysysDirectory, "Extensions")
	if not os.path.isdir(extensionsDirectory): os.mkdir(extensionsDirectory)
	directory_created(extensionsDirectory)
	sys.stdout.write("Created and registered %s \n" % extensionsDirectory)

	# Create the documents directory link in start menu -> programs -> PySys
	documentsDirectory = os.path.join(pysysDirectory, "Documentation")
	if not os.path.isdir(documentsDirectory): os.mkdir(documentsDirectory)
	directory_created(documentsDirectory)
	sys.stdout.write("Created and registered %s \n" % documentsDirectory)

	# Create a shortcut to the epydoc documentation
	filename = os.path.join(documentsDirectory, "PySys Epydoc.lnk")
	description = "Epydoc API Documentation for the PySys module"
	create_shortcut("%s/pysys-doc/index.html"%python_lib_dir, description, filename)
	file_created(filename)
	sys.stdout.write("Created and registered link to documentation\n")
		
	# Create a shortcut to the release notes
	filename = os.path.join(pysysDirectory, "Release Notes.lnk")
	description = "Release Notes for the PySys module"
	create_shortcut("%s/pysys-release.txt"%python_lib_dir, description, filename)
	file_created(filename)
	sys.stdout.write("Created and registered link to release notes\n")
		
	# Create a shortcut to the uninstaller
	filename = os.path.join(pysysDirectory, "Uninstall.lnk")
	description = "Uninstall the PySys module"
	create_shortcut("%s/RemovePySys.exe" %python_dir, description, filename, "-u %s/PySys-wininst.log" % python_dir)
	file_created(filename)
	sys.stdout.write("Created and registered link to uninstaller\n")
	
	
def printUsage():
	sys.stdout.write("\nUsage: %s [option]\n" % os.path.basename(sys.argv[0]))
	sys.stdout.write("    where option is one of;\n")
	sys.stdout.write(" 	  -install		   perform the post install steps\n")
	sys.stdout.write(" 	  -remove		   perform the post uninstall steps\n\n")
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
			sys.stderr.write("Unknown option: %s\n"%arg)
			sys.exit(0)
		arg_index += 1
