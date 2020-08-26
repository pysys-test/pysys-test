import unittest
import factorial

class TestFactorial(unittest.TestCase):

	def testFactorial(self):
		self.assertEqual(factorial.factorial(0), 1)
		self.assertEqual(factorial.factorial(1), 1)
		self.assertEqual(factorial.factorial(5), 120)
		self.assertRaises(ArithmeticError, lambda: factorial.factorial(-1))

