import broken
import unittest

class TestBroken(unittest.TestCase):

	def testAddOne(self):
		# This happens to work, but by accident
		self.assertEquals(broken.brokenAdder(5,1), 6)

	def testAddTwo(self):
		# This should fail
		self.assertEquals(broken.brokenAdder(3,2), 5)

