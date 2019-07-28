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
@undocumented: createDescriptors, loadDescriptors
"""
from __future__ import print_function
__all__ = [ "createDescriptors","console" ]

import os.path, logging

# if set is not available (>python 2.6) fall back to the sets module
try:  
	set  
except NameError:  
	import sets
	from sets import Set as set

from pysys.constants import *
from pysys.exceptions import UserError
from pysys.xml.project import Project

def loadDescriptors(dir=None):
	"""Load descriptor objects representing a set of tests to run for 
	the current project, returning the list.
	
	Deprecated, use L{pysys.xml.descriptor.DescriptorLoader} instead.
	
	@param dir: The parent directory to search for runnable tests
	@return: List of L{pysys.xml.descriptor.TestDescriptor} objects. 
	Caller must sort this list to ensure deterministic behaviour. 
	@rtype: list
	@raises UserError: Raised if no testcases can be found.
	
	"""
	if dir is None: dir = os.getcwd()
	loader = Project.getInstance().descriptorLoaderClass(Project.getInstance())
	return loader.loadDescriptors(dir)

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
	@return: List of L{pysys.xml.descriptor.TestDescriptor} objects
	@rtype: list
	@raises UserError: Raised if no testcases can be found or are returned by the requested input parameters
	
	"""
	project = Project.getInstance()
	
	descriptors = loadDescriptors(dir=dir)
	# must sort by id for range matching and dup detection to work deterministically
	descriptors.sort(key=lambda d: [d.id, d.file])
	
	supportMultipleModesPerRun = getattr(project, 'supportMultipleModesPerRun', '').lower()=='true'
	
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
		
		allmodes = {} # populate this as we go; could have used a set, but instead use a dict so we can check or capitalization mismatches easily at the same time; 
		#the key is a lowercase version of mode name, value is the canonical capitalized name
		
		modeincludesnone = ((MODES_ALL in modeincludes or MODES_PRIMARY in modeincludes or '' in modeincludes) and 
					(MODES_PRIMARY not in modeexcludes and '' not in modeexcludes))
		
		for d in descriptors:
			if not d.modes:
				# for tests that have no modes, there is only one descriptor and it's treated as the primary mode; 
				# user can also specify '' to indicate no mode
				if modeincludesnone:
					d.mode = None
					modedescriptors[d.id] = [d]
				else:
					modedescriptors[d.id] = []
			else:
				thisdescriptorlist = []
				modedescriptors[d.id] = thisdescriptorlist # even if it ends up being empty
				
				# create a copy of the descriptor for each selected mode
				for m in d.modes: 
					try:
						canonicalmodecapitalization = allmodes[m.lower()]
					except KeyError:
						allmodes[m.lower()] = m
					else:
						if m != canonicalmodecapitalization:
							# this is useful to detect early; it's almost certain to lead to buggy tests 
							# since people would be comparing self.mode to a string that might have different capitalization
							raise UserError('Cannot have multiple modes with same name but different capitalization: "%s" and "%s"'%(m, canonicalmodecapitalization))
					
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

		for m in [MODES_ALL, MODES_PRIMARY]:
			if m.lower() in allmodes: raise UserError('The mode name "%s" is reserved, please select another mode name'%m)
		
		# don't permit the user to specify a non existent mode by mistake
		for m in modeincludes+modeexcludes:
			if (not m) or m.upper() in [MODES_ALL, MODES_PRIMARY]: continue
			if allmodes.get(m.lower(),None) != m:
				raise UserError('Unknown mode "%s": the available modes for descriptors in this directory are: %s'%(
					m, ', '.join(sorted(allmodes.values() or ['<none>']))))
		
	# first check for duplicate ids
	ids = {}
	dups = []
	d = None
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
							if testspecmode not in descriptors[index].modes:
								raise UserError('Unknown mode "%s": the available modes for this test are: %s'%(
									testspecmode, ', '.join(sorted(descriptors[index].modes or ['<none>']))))

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
				elif '~' in t:
					# The utility of this would be close to zero and lots more to implement/test, so not worth it
					raise UserError('A ~MODE test mode selector can only be use with a test id, not a range or regular expression')
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
	
	# expand based on modes (unless we're printing in which case expandmodes=False)
	if supportMultipleModesPerRun and expandmodes: 
		expandedtests = []
		for t in tests:
			if hasattr(t, 'mode'): 
				# if mode if set it has no modes or has a test id~mode that was explicitly specified in a testspec, so does not need expanding
				expandedtests.append(t)
			else:
				expandedtests.extend(modedescriptors[t.id])
		tests = expandedtests
	
	# combine execution order hints from descriptors with global project configuration; 
	# we only need to do this if there are any executionOrderHints defined (may be pure group hints not for modes) 
	# or if there are any tests with multiple modes (since then the secondary hint mode delta applies)
	if (supportMultipleModesPerRun and len(allmodes)>0) or project.executionOrderHints:
		def calculateNewHint(d, mode):
			hint = d.executionOrderHint
			for hintdelta, hintmatcher in project.executionOrderHints:
				if hintmatcher(d.groups, mode): hint += hintdelta
			if mode: 
				hint += project.executionOrderSecondaryModesHintDelta * (d.modes.index(mode))
			return hint
		
		for d in tests:
			hintspermode = []
			if expandmodes: # used for pysys run; d.mode will have been set
				d.executionOrderHint = calculateNewHint(d, d.mode)
			else:
				modes = [None] if len(d.modes)==0 else d.modes
				# set this for the benefit of pysys print
				d.executionOrderHintsByMode = [calculateNewHint(d, m) for m in modes]
				d.executionOrderHint = d.executionOrderHintsByMode[0]
		
	if len(tests) == 0:
		raise UserError("The supplied options did not result in the selection of any tests")
	else:
		return tests


