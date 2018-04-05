def factorial(n):
	if n < 0:
		raise ArithmeticError('Factorial of negative number')
	elif n <= 1:
		return 1
	else:
		return factorial(n - 1) * n

