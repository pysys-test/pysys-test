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
A standalone utility script that recursively upgrades PySys tests from the old pysystest.xml+run.py format 
to the new pysystest.py format. XML comments are copied into the new file, and there is support for using 
your version control system's "move" commands to avoid losing the history of your existing run.py files. 
"""

import os.path, stat, getopt, logging, traceback, sys
import inspect
import xml.dom.minidom
import re

IGNORED_COMMENTS = [
	r"""<skipped reason=""/>""",
	r"""uncomment this to skip the test:
<skipped reason=""/>""",
	r"""To skip the test, uncomment this (and provide a reason): <skipped reason=""/>""",
	r"""To provide a bug/story/requirement id for requirements tracing, uncomment this: <requirement id=""/>""",
]

LINE_LENGTH_GUIDE = '=' * 80
DEFAULT_AUTHORS = ""
DEFAULT_CREATED = None

allwarnings = []

def xmlToPy(xmlpath):
	pypath = xmlpath[:-4]+'.py'
	d = {}
	comments = []
	groupsinherit = ['true']
	modesinherit = ['true']
	oldmodes = []
	d['user_data'] = {}

	warnings = [] # warnings


	doc = xml.dom.minidom.parse(xmlpath)
	root = doc.getElementsByTagName('pysystest')[0]
	def visitNode(n):
		if n.nodeType==n.COMMENT_NODE:
			t = re.sub(' +$', '', inspect.cleandoc(n.data).strip().replace('\t', '  '), flags=re.MULTILINE)
			if t and t not in IGNORED_COMMENTS: comments.append(t)
			return
		if n.nodeType!=n.ELEMENT_NODE: return
		
		# extract the text
		t = u''
		for cn in n.childNodes:
			if (cn.nodeType in [n.TEXT_NODE, n.CDATA_SECTION_NODE]) and cn.data:
				t += cn.data
		t = t.strip()
		
		tag = n.tagName
		if tag == 'pysystest':
			d['authors'] = n.getAttribute('authors') or DEFAULT_AUTHORS
			d['created'] = n.getAttribute('created') or DEFAULT_CREATED
			d['type'] = n.getAttribute('type')
			if n.getAttribute('state') == 'skipped':
				n['skipped_reason'] = 'Skipped (reason not specified)'
			elif n.getAttribute('state') == 'deprecated':
				warnings.append(f'state=deprecated was removed during migration since it is no longer supported in pysystest.py')
		elif tag == 'id-prefix':
			if t:
				warnings.append(f'Ignored id-prefix="{t}" as these are only supported at the pysysdirconfig.xml level for pysystest.py files')
		elif tag.replace('-dir','') in 'title,purpose,input,output,reference'.split(','):
			d[tag.replace('-dir','')] = t
		elif tag == 'skipped':
			d['skipped_reason'] = n.getAttribute('reason')
		elif tag == 'groups':
			groupsinherit = [(n.getAttribute('inherit') or 'true').lower()]
			if n.getAttribute('groups'):
				d['groups'] = n.getAttribute('groups')
		elif tag == 'group':
				if t: d['groups'] = d.get('groups','')+','+t
		elif tag == 'modes':
			if t.startswith('lambda'): 
				d['modes'] = t
			else:
				modesinherit = [(n.getAttribute('inherit') or 'true').lower()]
		elif tag == 'mode':
			if t: oldmodes.append(t)
		elif tag == 'execution-order':
			d['execution_order_hint'] = n.getAttribute('hint')
		elif tag == 'class':
			d['python_class'] = n.getAttribute('name')
			if d.get('python_class')=='PySysTest': del d['python_class']
			d['python_module'] = n.getAttribute('module')
			if d.get('python_module') in ['run', 'run.py']: del d['python_module']
		elif tag == 'user-data':
			d['user_data'][n.getAttribute('name')] = n.getAttribute('value') or t
		elif tag == 'requirement':
			if n.getAttribute('id'):
				d['requirements'] = d.get('requirements', [])+[n.getAttribute('id')]
		elif tag in 'description,classification,data,traceability,requirements'.split(','):
			pass
		else:
			assert False, 'Unexpected element: %s'%tag
		for cn in n.childNodes: visitNode(cn)
			
	visitNode(root)
	
	if d.pop('type','') == 'manual' and 'manual' not in d.get('groups',''): 
		d['groups'] = d.get('groups','')+',manual'
		warnings.append(f'type=manual was converted to a group during migration since the type= attribute is no longer supported in pysystest.py')

	if d.get('groups') or groupsinherit[0].lower()!='true': d['groups'] = ', '.join(x.strip() for x in d.get('groups','').split(',') if x.strip())+'; inherit='+groupsinherit[0]
	if d.get('user_data'): d['user_data'] = repr(d['user_data'])
		

	doc.unlink()

	if oldmodes: 
		if any(m[0].islower() for m in oldmodes):
				warnings.append(f'Some modes in this test start with a lowercase letter; these will be renamed to start with a capital letter (unless the enforceModeCapitalization=false project property is specified) - {oldmodes}')
		modes = 'lambda helper: '
		if modesinherit[0].lower() == 'true':
			modes += "helper.inheritedModes + "
		modes += repr([{'mode':m} for m in oldmodes])
		d['modes'] = modes
	
	def cleanIndentation(x):
		x = inspect.cleandoc(x)
		x = re.sub('^ +', lambda m: '\t'*(len(m.group(0))//8), x, flags=re.MULTILINE)
		return x.replace("\n","\n\t")
	
	py =  f'__pysys_title__   = r""" {d.pop("title", "")} """\n'
	py += f'#                        {LINE_LENGTH_GUIDE}\n\n'
	py += f'__pysys_purpose__ = r""" {cleanIndentation(d.pop("purpose", ""))}\n\t"""\n\n'
	
	value = d.pop('id-prefix', None)
	if value: f'__pysys_id_prefix__ = "{value}"\n'
	
	py += f'__pysys_authors__ = "{d.pop("authors","")}"\n'
	value = d.pop("created", None)
	if value: py += f'__pysys_created__ = "{value}"\n\n'
	
	value = d.pop("requirements", None)
	if value: py += f'__pysys_traceability_ids__ = "{", ".join(value)}"\n'
	py += f'{"#" if not d.get("groups") else ""}__pysys_groups__  = "{d.pop("groups","myGroup; inherit=true")}"\n'
	value = d.pop('modes', None)
	if value:
		py += f'__pysys_modes__            = r""" {cleanIndentation(value)} """'+'\n\n'
	
	value = d.pop('execution_order_hint', None)
	if value: py += f'__pysys_execution_order_hint__ = {value}\n'

	for x in [
		'__pysys_python_class__',
		'__pysys_python_module__',
		'__pysys_input_dir__',
		'__pysys_reference_dir__',
		'__pysys_output_dir__',
	]:
		key = x.replace('__pysys_','').replace('__','').replace('_dir','')
		value = d.pop(key, None)
		if value:
			py += f'{x} = "{value}"\n'

	value = d.pop('user_data', None)
	if value: py += f'__pysys_user_data__ = r""" {value} """\n\n'

	py += f'{"#" if not d.get("skipped_reason") else ""}__pysys_skipped_reason__   = "{d.pop("skipped_reason","Skipped until Bug-1234 is fixed")}"\n\n'

	assert not d, 'Internal error - unexpected items: %s'%repr(d)

	# add warnings as comments in the file
	for w in warnings:
		allwarnings.append(f'{w}: {pypath}')
		py += '# Warning from pysystest.xml->pysystest.py conversion: {w}'+'\n'
	if warnings: py += '\n'

	if comments:
		py += '# Comments copied from pysystest.xml (but original position of comments not retained):'+'\n\n'
		for c in comments:
			py += '# '+c.replace('\n', '\n# ')+'\n\n'
		allwarnings.append(f'XML comments were copied to end of the pysystest.py descriptor section but they probably need moving to the right position: {pypath}')

	return py, comments

def upgradeMain(args):

	options = [x for x in args if x.startswith('-')]
	args = [x for x in args if not x.startswith('-')]
	dryrun = '--dry-run' in options
	
	if (options and not dryrun) or len(args) != 2: 
		print('Unknown options or missing arguments'%options)
		print('')
		print('Automatically upgrade pysystest.xml+run.py all tests under the current directory to pysystest.py')
		print('Usage:')
		print('pysystestxml_upgrader.py [--dry-run] "DELETE CMD" "RENAME CMD"')
		print('')
		print('For example:')
		print('   pysystestxml_upgrader.py "rm" "mv"')
		print('   pysystestxml_upgrader.py "del" "move"')
		print('   pysystestxml_upgrader.py "svn rm" "svn mv"')
		print('   pysystestxml_upgrader.py "git rm" "git mv"')
		print('')
		print('Be sure to avoid having uncommitted changes in your working cooy before running this script.')
		print('This script uses tabs not spaces for indentation; fix up afterwards if you prefer spaces.')
		return 1

	deleter, renamer = args
	print(f'dry-run = {dryrun}, delete="{deleter}", rename="{renamer}"')
	
	count = 0
	errors = []
	allcomments = {}
	for (dirpath, dirnames, filenames) in os.walk('.'):
		dirnames.sort() # do this in a deterministic order
		if not ('pysystest.xml' in filenames and 'run.py' in filenames): continue
		print('Upgrading: %s'%dirpath)
		assert 'pysystest.py' not in filenames, dirpath
		
		with open(f'{dirpath+os.sep}run.py', 'rb') as f:
			runpy = f.read()
		
		xmlpath = os.path.normpath(f'{dirpath+os.sep}pysystest.xml')
		pysystestpath = xmlpath[:-4]+'.py'
		try:
			pydescriptor, comments = xmlToPy(xmlpath)
		except Exception as ex:
			traceback.print_exc()
			errors.append(f'Failed to extract descriptor from {xmlpath} - {ex}')
			continue
		
		for c in comments:
			allcomments[c] = allcomments.get(c, 0)+1
		
		runpyencoding = None
		try:
			pydescriptor.encode('ascii')
		except Exception as ex:
			runpyencoding = re.search(r"[ \t\f]*#.*?coding[:=][ \t]*([-_.a-zA-Z0-9]+)".encode('ascii'), runpy)
			if runpyencoding: runpyencoding = runpyencoding.group(1)
			runpyencoding = (runpyencoding or b'').decode('ascii').upper()
			if runpyencoding != 'UTF-8':
				try:
					runpy.decode('ascii')
				except:
					pass
				else:
					runpyencoding = 'ASCII'
				allwarnings.append(f'Non-ASCII characters found in descriptor will be added as UTF-8 to pysystest.py which uses encoding={runpyencoding or "unknown"}; this may need fixing up manually: {pysystestpath}')

		if dryrun: print(pydescriptor.replace('\t', '<tab>'))

		if not dryrun: 
			if os.system(f'{renamer} {dirpath+os.sep}run.py {dirpath+os.sep}pysystest.py') != 0: 
				errors.append(f'Failed to rename run.py to {pysystestpath}, aborting')
				break

			with open(pysystestpath, 'wb') as f:
				f.write(pydescriptor.replace('\n', os.linesep).encode(runpyencoding or 'UTF-8'))
				f.write(runpy)

			if os.system(f'{deleter} {xmlpath}') != 0: 
				errors.append(f'Failed to delete {xmlpath}, aborting')
				break
		sys.stdout.flush()
		
		count += 1
	
	with open('pysys_upgrader.log', 'w') as log:
		log.write(f'\nSuccessfully upgraded {count} tests under {os.getcwd()}\n')

		if allcomments:
			log.write(f'\n{len(allcomments)} unique comments found (more frequent last)\n')
			for c in sorted(allcomments, key=lambda x: allcomments[x]): log.write(f'  - {allcomments[c]} occurrences of: """{c}"""\n\n')

		log.write(f'\n{len(allwarnings)} warnings\n')
		for w in allwarnings: log.write(f'  {w}\n')

		log.write(f'\n{len(errors)} errors\n')
		for e in errors: log.write(f'  {e}\n')
		
	with open('pysys_upgrader.log', 'r') as log:
		sys.stdout.write(log.read())


sys.exit(upgradeMain(sys.argv[1:]) or 0)

