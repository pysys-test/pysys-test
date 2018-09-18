import sys
i = 0
for a in sys.argv[1:]:
	i+=1
	sys.stdout.write('arg: <%s>\n'%(a))
