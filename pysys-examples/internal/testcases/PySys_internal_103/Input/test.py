def myFunction(x):
	"""
	Doc string. 
	
	>>> myFunction(100)
	100

	>>> myFunction(200)
	200

	>>> myFunction('actual value')
	'expected wrong value'

	>>> myFunction('simulated failure')
	'correct value'
	
	>>> myFunction(300)
	300
	
	"""
	if x=='fail': raise Exception('simulated failure')
	return x