#!/usr/bin/env python
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and any associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# The software is provided "as is", without warranty of any
# kind, express or implied, including but not limited to the
# warranties of merchantability, fitness for a particular purpose
# and noninfringement. In no event shall the authors or copyright
# holders be liable for any claim, damages or other liability,
# whether in an action of contract, tort or otherwise, arising from,
# out of or in connection with the software or the use or other
# dealings in the software

import logging

from pysys import rootLogger
from pysys.constants import *
from pysys.exceptions import *

log = logging.getLogger('pysys.writer.console')
log.setLevel(logging.NOTSET)


class ConsoleResultsWriter:

	def __init__(self):
		pass
		
	def writeResults(self, results, **kwargs):
		if kwargs.has_key('totalDuration'):
			totalDuration = kwargs['totalDuration']
		else:
			totalDuration = "n/a"
			
		log.info("")
		log.info("Total duration: %.2f (secs)", totalDuration)		
		log.info("Summary of non passes: ")
		fails = 0
		for cycle in results.keys():
			for outcome in results[cycle].keys():
				if outcome in FAILS : fails = fails + len(results[cycle][outcome])
		if fails == 0:
			log.info("	THERE WERE NO NON PASSES")
		else:
			if len(results) == 1:
				for outcome in FAILS:
					for test in results[0][outcome]: log.info("  %s: %s ", LOOKUP[outcome], test)
			else:
				for key in results.keys():
					for outcome in FAILS:
						for test in results[key][outcome]: log.info(" [CYCLE %d] %s: %s ", key+1, LOOKUP[outcome], test)