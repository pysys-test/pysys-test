import os, glob
from pysys.constants import *
from pysys.basetest import BaseTest

class RPNBaseTest(BaseTest):

    def setup(self):
        BaseTest.setup(self)
        print glob.glob(os.path.join(PROJECT.root,'target','rpn-*.jar'))

    def startApplication(self):
        command = os.path.join(PROJECT.JAVA_HOME, 'bin', 'java')
        displayName = 'application'

        # set the default stdout and stderr
        instances = self.getInstanceCount(displayName)
        dstdout = "%s/application.out"%self.output
        dstderr = "%s/application.err"%self.output
        if instances: dstdout  = "%s.%d" % (dstdout, instances)
        if instances: dstderr  = "%s.%d" % (dstderr, instances)

        # setup args
        args=[]
        args.extend(['-jar', os.path.join(PROJECT.root,'target','rpn-1.0-SNAPSHOT.jar')])

        # run the process and return the handle
        pHandle = self.startProcess(command, args, os.environ, self.output, BACKGROUND, 0, dstdout, dstderr, displayName)
        self.waitForSignal('application.out', expr='org.pysys.examples.rpn.Application.*Started Application', timeout=10)
        return pHandle