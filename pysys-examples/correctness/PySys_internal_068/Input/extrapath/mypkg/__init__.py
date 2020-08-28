from pysys.writer import *
import logging

class ArtifactPrinter(BaseRecordResultsWriter, ArtifactPublisher):
	cleanedup = False
	def cleanup(self, **kwargs):
		self.cleanedup = True
		logging.getLogger('pysys.writer').info('--- ArtifactPrinter cleanup')

	def publishArtifact(self, path, category, **kwargs):
		assert not self.cleanedup, 'Should publish all artifacts before writer.cleanup' # some CI writers may need this
		
		logging.getLogger('pysys.writer').info('Published artifact %s: %s', category, path)
