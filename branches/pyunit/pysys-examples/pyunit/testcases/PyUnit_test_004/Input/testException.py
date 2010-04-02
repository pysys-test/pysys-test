import broken
import unittest

class TestException(unittest.TestCase):

	def testRaise(self):
		raise KeyError()

	def testAssert(self):
		assert False

