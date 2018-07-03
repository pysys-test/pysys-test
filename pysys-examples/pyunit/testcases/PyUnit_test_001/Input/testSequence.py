import random
import unittest

class TestSequence(unittest.TestCase):

	SIZE = 10
	
	def testReverse(self):
		s1 = list(range(self.SIZE))
		random.shuffle(s1)
		s2 = list(s1)
		s2.reverse()
		for i in range(self.SIZE):
			self.assertEqual(s1[i], s2[self.SIZE - i - 1])
		s2.reverse()
		self.assertEqual(s1, s2)

if __name__ == '__main__':
    unittest.main()

