fib= []
fib.append(0)
fib.append(1)

print "Calculating fibonacci series with ten entries"
for i in range(2, 10):
	fib.append(fib[i-1] + fib[i-2])

print "Writting fibonacci series to stdout"
for line in fib:
	print line