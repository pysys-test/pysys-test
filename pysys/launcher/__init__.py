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


"""
Contains utilities used by test launchers when running, printing, cleaning or making new tests. 

The module includes the L{pysys.launcher.createDescriptors} method which locates test 
descriptors based upon a given starting location on the file system, the chosen range 
of test ids, the test type, the specified requirements, and the include and exclude lists.

Utilities defined in the module can be used by any launchers, either distributed
with the framework, or created as an extension to it. Currently the framework 
distributes the console launcher module only - see L{pysys.launcher.console}. This 
module uses the current working directory in a command shell as the starting location 
on the file system, and provides utilities for parsing command line arguments in order
to launch operations against a set of tests etc.  

"""
from __future__ import print_function
__all__ = [ "createDescriptors","console" ]

import os.path, logging
import locale

# if set is not available (>python 2.6) fall back to the sets module
try:  
	set  
except NameError:  
	import sets
	from sets import Set as set

from pysys.constants import *
from pysys.xml.descriptor import XMLDescriptorParser
from pysys.utils.fileutils import toLongPathSafe, fromLongPathSafe, pathexists
from pysys.utils.pycompat import PY2
from pysys.exceptions import UserError

def loadDescriptors(dir=None):
	"""Load descriptor objects representing a set of tests to run, returning the list.
	
	@param dir: The parent directory to search for runnable tests
	@return: List of L{pysys.xml.descriptor.XMLDescriptorContainer} objects. 
	Caller must sort this list to ensure deterministic behaviour. 
	@rtype: list
	@raises UserError: Raised if no testcases can be found.
	
	"""
	descriptors = []
	descriptorfiles = []
	ignoreSet = set(OSWALK_IGNORES)
	descriptorSet =set(DEFAULT_DESCRIPTOR)
	
	if dir is None: dir = os.getcwd()
	projectfound = PROJECT.projectFile != None
	log = logging.getLogger('pysys.launcher')

	# although it's highly unlikely, if any test paths did slip outside the Windows 256 char limit, 
	# it would be very dangerous to skip them (which is what os.walk does unless passed a \\?\ path). 
	i18n_reencode = locale.getpreferredencoding() if PY2 and isinstance(dir, str) else None
	for root, dirs, files in os.walk(toLongPathSafe(dir)):
		intersection =  descriptorSet & set(files)
		if intersection: 
			descriptorpath = fromLongPathSafe(os.path.join(root, intersection.pop()))
			# PY2 gets messed up if we start passing unicode rather than byte str objects here, 
			# as it proliferates to all strings in each test
			if i18n_reencode is not None: descriptorpath = descriptorpath.encode(i18n_reencode) 
			descriptorfiles.append(descriptorpath)
			# if this is a test dir, it never makes sense to look at sub directories
			del dirs[:]
			continue
		
		thisignoreset = ignoreSet # sub-directories to be ignored
		
		for ignorefile in ['.pysysignore', 'pysysignore']:
			for d in dirs:
				if pathexists(os.path.join(root, d, ignorefile)):
					thisignoreset = set(thisignoreset) # copy on write (this is a rare operation)
					thisignoreset.add(d)
					log.debug('Skipping directory %s due to ignore file %s', root+os.sep+ignorefile)
		
		for ignore in (thisignoreset & set(dirs)): dirs.remove(ignore)
		if not projectfound:
			for p in DEFAULT_PROJECTFILE:
				if p in files:
					projectfound = True
					sys.stderr.write('WARNING: PySys project file was not found in directory the script was run from but does exist at "%s" (consider running pysys from that directory instead)\n'%os.path.join(root, p))

	DIR_CONFIG_DESCRIPTOR = 'pysysdirconfig.xml'
	if PROJECT.projectFile and os.path.normpath(dir).startswith(os.path.normpath(os.path.dirname(PROJECT.projectFile))):
		# find directory config descriptors between the project root and the testcase 
		# dirs. We deliberately use project dir not current working dir since 
		# we don't want descriptors to be loaded differently depending on where the 
		# tests are run from (i.e. should be independent of cwd). 
		dirconfigs = {}
		projectroot = os.path.dirname(PROJECT.projectFile).replace('\\','/').split('/')
	else:
		dirconfigs = None
		log.debug('Project file does not exist under "%s" so processing of %s files is disabled', dir, DIR_CONFIG_DESCRIPTOR)
	
	def getParentDirConfig(descriptorfile):
		if dirconfigs is None: return None
		testdir = os.path.dirname(descriptorfile).replace('\\','/').split('/')
		currentconfig = None
		for i in range(len(projectroot), len(testdir)):
			currentdir = '/'.join(testdir[:i])
			if currentdir in dirconfigs:
				currentconfig = dirconfigs[currentdir]
			else:
				if pathexists(currentdir+'/'+DIR_CONFIG_DESCRIPTOR):
					currentconfig = XMLDescriptorParser.parse(currentdir+'/'+DIR_CONFIG_DESCRIPTOR, istest=False, parentDirDefaults=currentconfig)
					log.debug('Loaded directory configuration descriptor from %s: \n%s', currentdir, currentconfig)
				dirconfigs[currentdir] = currentconfig
		return currentconfig
	
	for descriptorfile in descriptorfiles:
		parentconfig = getParentDirConfig(descriptorfile)
		try:
			descriptors.append(XMLDescriptorParser.parse(descriptorfile, parentDirDefaults=getParentDirConfig(descriptorfile)))
		except UserError:
			raise # no stack trace needed, will already include descriptorfile name
		except Exception as e:
			log.info('Failed to read descriptor: ', exc_info=True)
			raise Exception("Error reading descriptor file '%s': %s - %s" % (descriptorfile, e.__class__.__name__, e))
			
	return descriptors

def createDescriptors(testIdSpecs, type, includes, excludes, trace, dir=None, modeincludes=[], modeexcludes=[], expandmodes=True):
	"""Create a list of descriptor objects representing a set of tests to run, filtering by various parameters, returning the list.
	
	@param testIdSpecs: A list of strings specifying the set of testcase identifiers
	@param type: The type of the tests to run (manual | auto)
	@param includes: A list of test groups to include in the returned set
	@param excludes: A list of test groups to exclude in the returned set
	@param trace: A list of requirements to indicate tests to include in the returned set
	@param dir: The parent directory to search for runnable tests
	@param modeincludes: A list specifying the modes to be included; 
	must contain at most one entry unless supportMultipleModesPerRun=True. 
	@param modeexcludes: A list specifying the modes to be excluded; 
	only supported if supportMultipleModesPerRun=True. 
	@param expandmodes: Set to False to disable expanding a test with multiple
	modes into separate descriptors for each one (used for pysys print) 
	if supportMultipleModesPerRun=True. 
	@return: List of L{pysys.xml.descriptor.XMLDescriptorContainer} objects
	@rtype: list
	@raises UserError: Raised if not testcases can be found or are returned by the requested input parameters
	
	"""
	descriptors = loadDescriptors(dir=dir)
	# must sort by id for range matching and dup detection to work deterministically
	descriptors.sort(key=lambda d: [d.id, d.file])
	
	supportMultipleModesPerRun = getattr(PROJECT, 'supportMultipleModesPerRun', '').lower()=='true'
	
	# as a convenience support !mode syntax in the includes
	modeexcludes = modeexcludes+[x[1:] for x in modeincludes if x.startswith('!')]
	modeincludes = [x for x in modeincludes if not x.startswith('!')]
	for x in modeexcludes: 
		if x.startswith('!'): raise UserError('Cannot use ! in a mode exclusion: "%s"'%x)
		
	if not supportMultipleModesPerRun: 
		if len(modeincludes)>1: raise UserError('Cannot specify multiple modes unless supportMultipleModesPerRun=True')
		if modeexcludes: raise UserError('Cannot specify mode exclusions unless supportMultipleModesPerRun=True')
	else: 
		# populate modedescriptors data structure for supportMultipleModesPerRun=True
		MODES_ALL = 'ALL'
		MODES_PRIMARY = 'PRIMARY'
		assert MODES_ALL not in modeexcludes, "Cannot exclude all modes, that doesn't make sense"
		if not modeincludes: # pick a useful default
			if modeexcludes:
				modeincludes = [MODES_ALL]
			else:
				modeincludes = [MODES_PRIMARY]

		modedescriptors = {} # populate this with testid:[descriptors list]
		for d in descriptors:
			if not d.modes:
				# for tests that have no modes, there is only one descriptor and it's treated as the primary mode; 
				# user can also specify '' to indicate no mode
				if ((MODES_ALL in modeincludes or MODES_PRIMARY in modeincludes or '' in modeincludes) and 
					(MODES_PRIMARY not in modeexcludes and '' not in modeexcludes)):
					d.mode = None
					modedescriptors[d.id] = [d]
				else:
					modedescriptors[d.id] = []
			else:
				thisdescriptorlist = []
				modedescriptors[d.id] = thisdescriptorlist # even if it ends up being empty
				
				# create a copy of the descriptor for each selected mode
				for m in d.modes: 
					if m in [MODES_ALL, MODES_PRIMARY]: raise UserError('The mode name "%s" is reserved, please select another mode name'%m)
					# apply modes filter
					isprimary = m==d.primaryMode
					
					# excludes 
					if isprimary and MODES_PRIMARY in modeexcludes: continue
					if m in modeexcludes: continue
					
					# includes
					if not (MODES_ALL in modeincludes or 
						m in modeincludes or 
						(isprimary and MODES_PRIMARY in modeincludes)
						): 
						continue
					
					thisdescriptorlist.append(d._createDescriptorForMode(m))
	
	# first check for duplicate ids
	ids = {}
	dups = []
	for d in descriptors:
		if d.id in ids:
			dups.append('%s - in %s and %s'%(d.id, ids[d.id], d.file))
		else:
			ids[d.id] = d.file
	if dups:
		dupmsg = 'Found %d duplicate descriptor ids: %s'%(len(dups), '\n'.join(dups))
		if os.getenv('PYSYS_ALLOW_DUPLICATE_IDS','').lower()=='true':
			logging.getLogger('pysys').warn(dupmsg) # undocumented option just in case anyone complains
		else:
			raise UserError(dupmsg)
	

	# trim down the list for those tests in the test specifiers 
	# unless user the testspec includes a mode suffix, this stage ignores modes, 
	# and then we expand the modes out afterwards
	tests = []
	if testIdSpecs == []:
		tests = descriptors
	else:
		testids = set([d.id for d in descriptors])
		def idMatch(descriptorId, specId):
			if specId==descriptorId: return True
			
			# permit specifying suffix at end of testcase, which is 
			# important to allow shell directory completion to be used if an id-prefix is 
			# being added onto the directory id; but only do this if spec is non-numeric 
			# since we don't want to match test_104 against spec 04
			if specId.isdigit():
				return re.match('.+_0*%s$'%re.escape(specId), descriptorId)
			else:
				return descriptorId.endswith(specId) and specId not in testids

		for t in testIdSpecs:
			try:
				matches = None
				index = index1 = index2 = -1
				t = t.rstrip('/\\')

				if re.search('^[\w_.~]*$', t): # single test id (not a range or regex)
					if '~' in t:
						testspecid, testspecmode = t.split('~')
						# first match the id, then the mode
						for i in range(0,len(descriptors)):
							if idMatch(descriptors[i].id, testspecid): 
								index = i
								break
						if index >= 0:
							matches = [descriptors[index]._createDescriptorForMode(testspecmode)]
							# note test id+mode combinations selected explicitly like this way are included regardless of what modes are enabled/disabled

					else: # normal case where it's not a mode
						for i in range(0,len(descriptors)):
							if idMatch(descriptors[i].id, t): 
								index = i
								break
						matches = descriptors[index:index+1]
						if supportMultipleModesPerRun and not modedescriptors[matches[0].id]:
							# if user explicitly specified an individual test and excluded all modes it can run in, 
							# we shouldn't silently skip/exclude it as they clearly made a mistake
							raise UserError('Test "%s" cannot be selected with the specified mode(s).'%matches[0].id)

				# numeric ranges (inline mode specifiers not permitted from here on, in the interests of simplicity)
				elif re.search('^:[\w_.]*', t):
					for i in range(0,len(descriptors)):
						if idMatch(descriptors[i].id, t.split(':')[1]): index = i
					matches = descriptors[:index+1]

				elif re.search('^[\w_.]*:$', t):
					for i in range(0,len(descriptors)):
					  	if idMatch(descriptors[i].id, t.split(':')[0]): index = i
					matches = descriptors[index:]

				elif re.search('^[\w_.]*:[\w_.]*$', t):
					for i in range(0,len(descriptors)):
					  	if idMatch(descriptors[i].id, t.split(':')[0]): index1 = i
					  	if idMatch(descriptors[i].id, t.split(':')[1]): index2 = i
					matches = descriptors[index1:index2+1]

				else: 
					# regex match
					matches = [descriptors[i] for i in range(0,len(descriptors)) if re.search(t, descriptors[i].id)]

				# each specified test patten must match something, else probably user made a typo
				if not matches: raise Exception("No matches for: '%s'", t)
				tests.extend(matches)

			except UserError:
				raise
			except Exception:
				raise UserError("Unable to locate requested testcase(s): '%s'"%t)
				
	# trim down the list based on the type
	if type:
		index = 0
		while index != len(tests):
			if type != tests[index].type:
				tests.pop(index)
			else:
				index = index + 1
			
	# trim down the list based on the include and exclude groups
	if len(excludes) != 0:
		index = 0
		while index != len(tests):
			remove = False

			for exclude in excludes:
				if exclude in tests[index].groups:
					remove = True
					break

			if remove:
				tests.pop(index)
			else:
				index = index +1
				
	if includes != []:
		index = 0
		while index != len(tests):
			keep = False
				
			for include in includes:
				if include in tests[index].groups:
					keep = True
					break

			if not keep:
				tests.pop(index)
			else:
				index = index +1

	# trim down the list based on the traceability
	if trace:
		index = 0
		while index != len(tests):
			if trace not in tests[index].traceability :
				tests.pop(index)
			else:
				index = index + 1
	
	# expand based on modes
	if supportMultipleModesPerRun and expandmodes: 
		expandedtests = []
		for t in tests:
			if getattr(t, 'mode', None): # this indicates a test id~mode that was explicitly specified, so does not need expanding
				expandedtests.append(t)
			else:
				expandedtests.extend(modedescriptors[t.id])
		tests = expandedtests
	
	if len(tests) == 0:
		raise UserError("The supplied options did not result in the selection of any tests")
	else:
		return tests


