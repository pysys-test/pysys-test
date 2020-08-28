import random
import unittest

class TestSet(unittest.TestCase):

	def testIntersection(self):
		s1 = set('abc')
		s2 = set('cde')
		self.assertEqual(s1.intersection(s2), set('c'))

	def testUnion(self):
		s1 = set('abc')
		s2 = set('cde')
		self.assertEqual(s1.union(s2), set('abcde'))

if __name__ == '__main__':
    unittest.main()

