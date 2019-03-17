#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2019 M.B. Grieve

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



import os, shutil

def mkdir(path):
	"""
	Create a directory, with recursive creation of any parent directories.
	
	This function is a no-op (does not throw) if the directory already exists. 
	
	"""
	try:
		os.makedirs(path)
	except Exception as e:
		if not os.path.isdir(path):
			raise

def deletedir(path):
	"""
	Recursively delete the specified directory. 
	
	Does nothing if it does not exist. Raises an exception if the deletion fails. 
	"""
	try:
		shutil.rmtree(path)
	except Exception:
		if not os.path.exists(path): return # nothing to do
		raise
