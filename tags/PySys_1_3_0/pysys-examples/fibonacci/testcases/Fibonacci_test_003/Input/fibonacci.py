import sys
fib= []
fib.append(0)
fib.append(1)

sys.stdout.write("Calculating fibonacci series with ten entries\n")
for i in range(2, 10):
	fib.append(fib[i-1] + fib[i-2])

sys.stdout.write("Writting fibonacci series to stdout\n")
for line in fib:
	sys.stdout.write('%s\n'%line)