from twisted.internet import reactor
from twisted.internet import protocol
import os
import json

from pipeline import PipelineStatusEvent, PipelineFactory

class SlicerProcessJobManager():
    """This class should implement Pyslicer's own process manager. Pyslicer still uses Slicer's process manager as of now."""
    # Keep the original code of this class as of now
    def __init__(self, tmpDirRoot, slicerPath, proxyurl):
        self.jobs = {}
        #self.processCount = 0
        self.tmpDirRoot = tmpDirRoot
        self.slicerPath = slicerPath
        self.proxyurl = proxyurl

#    def getNextJobId(self):
#        # could be problematic if multithreaded
#        jobId = self.processCount
#        self.processCount = self.processCount + 1
#        self.jobs[str(jobId)] = {}
#        return jobId 
    def addJob(self, jobId):
        self.jobs[str(jobId)] = {}

    def processEvent(self, event):
        pass
        #jobEvents = self.jobs[str(event.jobId)]
        #jobEvents[event.eventId] = event

    def getStatus(self, jobId=None):
        print "getStatus", jobId
        print self.jobs
        if jobId is not None and jobId in self.jobs:
            status = str(jobId) +":"+ str(sorted(self.jobs[jobId].values(), key=lambda event: int(event.eventId)))
        else:
            #status = ''
            #for jobId, jobEvents in self.jobs.items():
            #    jobEvents = [str(event) for event in sorted(jobEvents.values(), key=lambda event: int(event.eventId))]
            #    status = str(jobEvents)
            status = ""
        return status

class SlicerProcess(protocol.ProcessProtocol):
    """This class implements a twisted process which runs a python script within
     Slicer's Python environment."""
    def __init__(self, jobManager, jobId, pipelineName, requestArgs):
        self.jobManager = jobManager
        self.jobId = jobId
        self.jobManager.addJob(jobId)
        self.pipelineName = pipelineName
        self.requestArgs = requestArgs
        self.data = ""
        self.err = ""
        self.events = {}

    def connectionMade(self):
        print str(self.jobId) + "connectionMade!"
        self.transport.closeStdin() # tell them we're done

    def outReceived(self, data):
        #print str(self.jobId) + "outReceived! with %d bytes!" % len(data)
        # look for status events
        self.data = self.data + data
        print data
        event = PipelineStatusEvent.parseEvent(data)
        if event is not None:
            self.jobManager.processEvent(event)

    def errReceived(self, data):
        print str(self.jobId) + "errReceived! with %d bytes!" % len(data)
        self.err = self.err + data

    def inConnectionLost(self):
        print str(self.jobId) + "inConnectionLost! stdin is closed! (we probably did it)"

    def outConnectionLost(self):
        print str(self.jobId) + "outConnectionLost! The child closed their stdout!"
        # now is the time to examine what they wrote
        print "len:", len(self.data)
        lines = self.data.split('\n')
        print len(lines)
        for line in lines:
            event = PipelineStatusEvent.parseEvent(line)
            if event is not None:
                self.jobManager.processEvent(event)

    def errConnectionLost(self):
        print str(self.jobId) + "errConnectionLost! The child closed their stderr."
        print self.err

    def processExited(self, reason):
        print str(self.jobId) + "processExited, status %d" % (reason.value.exitCode,)

    def processEnded(self, reason):
        print str(self.jobId) + "processEnded, status %d" % (reason.value.exitCode,)

    def run(self):
        """Trigger the slicer job by running a python script in Slicer's environment"""
        xvfbLogfile = os.path.join(self.jobManager.tmpDirRoot, 'xvfb.log')
        xvfbCmdParts = ['xvfb-run', '-a', '-e', xvfbLogfile]
        slicerArgs = ['--no-main-window', '--python-script']
        # Get name of the python script for the pipeline
        pipelinefactory = PipelineFactory()
        slicerPythonScript = pipelinefactory.getSlicerScript(self.pipelineName)
        # Input parameters from the HTTP request
        jsonArgs = json.dumps(self.requestArgs)
        print [str(self.jobId), self.jobManager.tmpDirRoot, jsonArgs]
        # Slicer job in command line
        slicerCmdParts = [self.jobManager.slicerPath] + slicerArgs + \
            [slicerPythonScript] + [str(self.jobId), self.jobManager.tmpDirRoot, jsonArgs]
        cmd = xvfbCmdParts + slicerCmdParts  
        print str(self.jobId) + " run: " + str(cmd)
        print ">>>>>>>>>>>>>>>SlicerProcess running:",str(cmd)
        # TODO: Ensure that the proper xvfb-run is invoked
        reactor.spawnProcess(self, 'xvfb-run', cmd, env=os.environ, usePTY=True)

