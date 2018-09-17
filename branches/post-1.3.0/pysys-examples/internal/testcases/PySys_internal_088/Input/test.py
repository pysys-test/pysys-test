import sys
i = 0
for a in sys.argv:
	i+=1
	sys.stdout.write('arg: <%s>\n'%(a))
