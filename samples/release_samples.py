#!/usr/bin/env python3

# Script for building the PySys samples into a form that can be committed to the GitHub sample repos, by copying 
# common files and setting permissions

import shutil, os, subprocess, shlex, time
samplesdir = os.path.dirname(__file__)

os.chdir(samplesdir)
print(f'Building samples under {os.getcwd()}')

builddir =  '__release_samples'
if os.path.exists(builddir): 
	try:
		shutil.rmtree(builddir)
	except:
		os.rename(builddir, builddir+'.%s'%time.time())
def copyFileOrDir(src, dest):
	if os.path.basename('src') == '.git': return
	if os.path.isdir(src):
		shutil.copytree(src, dest)
	else:
		shutil.copy2(src, dest)
def git(args, **kwargs):
	return subprocess.check_call(['git']+shlex.split(args), **kwargs)

for sample in ['getting-started', 'cookbook']:
	os.chdir(samplesdir)
	print('--- Building: '+sample)
	git(f'clone https://github.com/pysys-test/sample-{sample}.git {builddir}/{sample}') #--branch main 
	
	# remove old files
	for p in os.listdir(f'{builddir}/{sample}'):
		if p == '.git': continue
		p = f'{builddir}/{sample}/{p}'
		if os.path.isdir(p):
			shutil.rmtree(p)
		else:
			os.remove(p)
		
	# copy in new files
	# hopefully no Output or __ dirs, but if there are they should be dealt with by our .gitignore
	for p in os.listdir(sample):
		copyFileOrDir(f'{sample}/{p}', f'{builddir}/{sample}/{p}')
	
	# copy in shared files
	for p in os.listdir('common-files'):
		copyFileOrDir(f'common-files/{p}', f'{builddir}/{sample}/{p}')

	# stage the changes
	os.chdir(builddir+'/'+sample)
	git('add -A')
	for exe in ['bin/my_server.sh']:
		if os.path.exists(exe):
			git(f'add --chmod=+x {exe}')
	git('status')
	print('')
os.chdir(samplesdir)
print (f'\nRepos have been created under {builddir}. Now commit the changes and push.')
print ("IMPORTANT: push sample-getting-started after other samples as the most recently updated appears earlier in the project list")
print ('To verify: 1) check that the GitHub Actions passes and 2) check the readme looks OK in GitHub rendering and all the links work')
