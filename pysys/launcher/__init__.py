#!/usr/bin/env python
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
Implementation of the pysys.py command line launcher.
"""
from __future__ import print_function
__all__ = [ "createDescriptors","console" ]

import os.path, logging

from pysys.constants import *
from pysys.exceptions import UserError
from pysys.config.project import Project

def loadDescriptors(dir=None):
	"""Load descriptor objects representing a set of tests to run for 
	the current project, returning the list.
	
	:meta private: Deprecated and since 1.5.1 also hidden; use `pysys.config.descriptor.DescriptorLoader` instead.
	
	:param dir: The parent directory to search for runnable tests
	:return: List of L{pysys.config.descriptor.TestDescriptor} objects. 
		Caller must sort this list to ensure deterministic behaviour. 
	:rtype: list
	:raises UserError: Raised if no testcases can be found.
	
	"""
	if dir is None: dir = os.getcwd()
	loader = Project.getInstance().descriptorLoaderClass(Project.getInstance())
	return loader.loadDescriptors(dir)

TEST_ID_CHARS = r'-_.\w' # internal API, subject to change at any time, do not use
MODE_CHARS = TEST_ID_CHARS+'~=' # internal API, subject to change at any time, do not use

def createDescriptors(testIdSpecs, type, includes, excludes, trace, dir=None, modeincludes=[], modeexcludes=[], expandmodes=True):
	"""Create a list of descriptor objects representing a set of tests to run, filtering by various parameters, returning the list.
	
	:meta private: Not for use outside the framwork. 
	
	:param testIdSpecs: A list of strings specifying the set of testcase identifiers
	:param type: The type of the tests to run (manual | auto)
	:param includes: A list of test groups to include in the returned set
	:param excludes: A list of test groups to exclude in the returned set
	:param trace: A list of requirements to indicate tests to include in the returned set
	:param dir: The parent directory to search for runnable tests
	:param modeincludes: A list specifying the modes to be included. 
	:param modeexcludes: A list specifying the modes to be excluded. 
	:param expandmodes: Set to False to disable expanding a test with multiple
		modes into separate descriptors for each one (used for pysys print). 
	:return: List of L{pysys.config.descriptor.TestDescriptor} objects
	:rtype: list
	:raises UserError: Raised if no testcases can be found or are returned by the requested input parameters
	
	"""
	project = Project.getInstance()
	
	descriptors = loadDescriptors(dir=dir)
	# must sort by id for range matching and dup detection to work deterministically
	descriptors.sort(key=lambda d: [d.id, d.file])
	
	# as a convenience support !mode syntax in the includes
	modeexcludes = modeexcludes+[x[1:] for x in modeincludes if x.startswith('!')]
	modeincludes = [x for x in modeincludes if not x.startswith('!')]
	for x in modeexcludes: 
		if x.startswith('!'): raise UserError('Cannot use ! in a mode exclusion: "%s"'%x)
	
	# populate modedescriptors data structure
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

	NON_MODE_CHARS = '[^'+MODE_CHARS+']'
	def isregex(m): return re.search(NON_MODE_CHARS, m)

	regexmodeincludes = [re.compile(m, flags=re.IGNORECASE) for m in modeincludes if isregex(m)]
	regexmodeexcludes = [re.compile(m, flags=re.IGNORECASE) for m in modeexcludes if isregex(m)]
	
	for d in descriptors:
		if not d.modes:
			# for tests that have no modes, there is only one descriptor and it's treated as the primary mode; 
			# user can also specify '' to indicate no mode
			if modeincludesnone:
				if expandmodes: d.mode = None
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
				isprimary = getattr(m, 'isPrimary', False) # use getattr in case a pre-2.0 str has crept in from a custom DescriptorLoader
				
				# excludes 
				if isprimary and MODES_PRIMARY in modeexcludes: continue
				if m in modeexcludes or any(regex.match(m) for regex in regexmodeexcludes): continue
				
				
				# includes
				if not (MODES_ALL in modeincludes or 
					m in modeincludes or 
					any(regex.match(m) for regex in regexmodeincludes) or
					(isprimary and MODES_PRIMARY in modeincludes)
					): 
					continue
				
				thisdescriptorlist.append(d._createDescriptorForMode(m))

	for m in [MODES_ALL, MODES_PRIMARY]:
		if m.lower() in allmodes: raise UserError('The mode name "%s" is reserved, please select another mode name'%m)
	
	# don't permit the user to specify a non existent mode by mistake
	for m in modeincludes+modeexcludes:
		if (not m) or m.upper() in [MODES_ALL, MODES_PRIMARY]: continue
		if isregex(m):
			if any(re.search(m, x, flags=re.IGNORECASE) for x in allmodes): continue
		else:
			if allmodes.get(m.lower(),None) == m: continue
		
		raise UserError('Unknown mode (or mode regex) "%s"; the available modes for descriptors in this directory are: %s'%(
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
			logging.getLogger('pysys').warning(dupmsg) # undocumented option just in case anyone complains
		else:
			raise UserError(dupmsg)
	

	# trim down the list for those tests in the test specifiers 
	# unless user the testspec includes a mode suffix, this stage ignores modes, 
	# and then we expand the modes out afterwards
	tests = []
	if testIdSpecs == []:
		tests = descriptors
	else:
		testids = {d.id: index for index, d in enumerate(descriptors)}
		def findMatchingIndex(specId): # change this to return the match, rather than whether it matches
			# optimize the case where we specify the full id; no need to iterate
			index = testids.get(specId, None)
			if index is not None: return index
			
			if specId.isdigit():
				regex = re.compile('.+_0*'+(specId.lstrip('0') if (len(specId)>0) else specId)+'$')
				matches = [index for index, d in enumerate(descriptors) if regex.match(d.id)]
			else:
				# permit specifying suffix at end of testcase, which is 
				# important to allow shell directory completion to be used if an id-prefix is 
				# being added onto the directory id; but only do this if spec is non-numeric 
				# since we don't want to match test_104 against spec 04
			
				matches = [index for index, d in enumerate(descriptors) if d.id.endswith(specId)]
			
			if len(matches) == 1: return matches[0]			
			if len(matches) == 0: raise UserError('No tests found matching id: "%s"'%specId)
			
			# as a special-case, see if there's an exact match with the dirname
			dirnameMatches = [index for index, d in enumerate(descriptors) if os.path.basename(d.testDir)==specId]
			if len(dirnameMatches)==1: return dirnameMatches[0]
			
			# nb: use space not comma as the delimiter so it's easy to copy paste it
			raise UserError('Multiple tests found matching "%s"; please specify which one you want: %s'%(specId, 
				' '.join([descriptors[index].id for index in matches[:20] ])))

		for t in testIdSpecs:
			try:
				matches = None
				index = index1 = index2 = None
				t = t.rstrip('/\\')

				if re.search(r'^[%s]*$'%MODE_CHARS, t): # single test id (not a range or regex)
					if '~' in t:
						testspecid, testspecmode = t.split('~')
						index = findMatchingIndex(testspecid)
						# first match the id, then the mode
						matchingmode = next((m for m in descriptors[index].modes if m == testspecmode), None)
						if matchingmode is None:
							raise UserError('Unknown mode "%s": the available modes for this test are: %s'%(
								testspecmode, ', '.join(sorted(descriptors[index].modes or ['<none>']))))

						matches = [descriptors[index]._createDescriptorForMode(matchingmode)]
						# note test id+mode combinations selected explicitly like this way are included regardless of what modes are enabled/disabled

					else: # normal case where it's not a mode
						index = findMatchingIndex(t)
						matches = descriptors[index:index+1]
						if not modedescriptors[matches[0].id]:
							# if user explicitly specified an individual test and excluded all modes it can run in, 
							# we shouldn't silently skip/exclude it as they clearly made a mistake
							raise UserError('Test "%s" cannot be selected with the specified mode(s).'%matches[0].id)
				elif '~' in t:
					# The utility of this would be close to zero and lots more to implement/test, so not worth it
					raise UserError('A ~MODE test mode selector can only be use with a test id, not a range or regular expression')
				elif re.search('^:[%s]*'%TEST_ID_CHARS, t):
					index = findMatchingIndex(t.split(':')[1])
					matches = descriptors[:index+1]

				elif re.search('^[%s]*:$'%TEST_ID_CHARS, t):
					index = findMatchingIndex(t.split(':')[0])
					matches = descriptors[index:]

				elif re.search('^[%s]*:[%s]*$'%(TEST_ID_CHARS,TEST_ID_CHARS), t):
					index1 = findMatchingIndex(t.split(':')[0])
					index2 = findMatchingIndex(t.split(':')[1])
					if index1 > index2:
						index1, index2 = index2, index1
					matches = descriptors[index1:index2+1]

				else: 
					# regex match
					try:
						matches = [descriptors[i] for i in range(0,len(descriptors)) if re.search(t, descriptors[i].id)]
					except Exception as ex:
						raise UserError('"%s" contains characters not valid in a test id, but isn\'t a valid regular expression either: %s'%(t, ex))
					if not matches: raise UserError("No test ids found matching regular expression: \"%s\""%t)

				if not matches: raise UserError("No test ids found matching: \"%s\""%st)
				tests.extend(matches)

			except UserError:
				raise
			except Exception:
				raise # this shouldn't be possible so no need to sugar coat the error message

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

	# expand based on modes (unless we're printing without any mode filters in which case expandmodes=False)
	if expandmodes: 
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
	if (len(allmodes)>0) or project.executionOrderHints:
		def calculateNewHint(d, mode):
			hint = d.executionOrderHint
			for hintdelta, hintmatcher in project.executionOrderHints:
				if hintmatcher(d.groups, mode): hint += hintdelta
			if mode and not getattr(mode, 'isPrimary', False): # bit of a fudge in the case of isPrimary!=(index==0) but good enough
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


