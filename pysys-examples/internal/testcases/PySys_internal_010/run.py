from pysys.utils.filereplace import replace
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		inputFile = "%s/input.txt" % self.input
		
		dict={"BIRD":"moorcock", "GILES":"farmer"}
		replace(inputFile, "%s/output1.txt" % self.output, dict, marker='$')

		dict={"CEREAL":"grain"}
		replace(inputFile, "%s/output2.txt" % self.output, dict, marker='%')
		
		dict={"$BIRD$":"moorcock", "$GILES$":"farmer", "%CEREAL%":"grain", "replaceme":"night"}
		replace(inputFile, "%s/output3.txt" % self.output, dict, marker='')
		
			
	def validate(self):
		# validate the correct replacement with the $ marker
		self.assertDiff("output1.txt", "ref_output1.txt")
		
		
