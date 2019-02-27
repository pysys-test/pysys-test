import factorial
import unittest

def negativeFactorial():
	return factorial.factorial(-1)

class TestFactorial(unittest.TestCase):

	def testFactorial(self):
		self.assertEqual(factorial.factorial(0), 1)
		self.assertEqual(factorial.factorial(1), 1)
		self.assertEqual(factorial.factorial(5), 120)
		self.assertRaises(ArithmeticError, negativeFactorial)

