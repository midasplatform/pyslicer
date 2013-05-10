import os
import urllib2
import urllib

class SlicerJob():
    """This class implements the base class for python jobs excuted within Slicer's Python environment."""
    event_process = "Process"
    event_exception = "Exception"

    def __init__(self, jobId, pipelineName, pydasParams, tmpDirRoot, dataDir, outDir, proxyurl):
        self.jobId = jobId
        self.pipelineName = pipelineName
        self.pydasParams = pydasParams
        self.tmpdirpath = tmpDirRoot
        self.dataDir = os.path.join(tmpDirRoot, dataDir)
        self.outDir = os.path.join(tmpDirRoot, outDir)
        self.proxyurl = proxyurl
    
    def report_status(self, eventType, message):
        args = {}
        args['pipeline'] = self.pipelineName
        args['job_id'] = self.jobId
        (args['email'], args['apikey'], args['url']) = self.pydasParams
        args['event_type'] = eventType
        args['message'] = message
        data = urllib.urlencode(args)
        request = urllib2.Request(self.proxyurl + "slicerjob/reportstatus?" + data)
        response = urllib2.urlopen(request)
        print response
    
    def jobEndingNotification(self, args=None):
        if args is not None:
            reqArgs = args.copy()
        else:
            reqArgs = {}
        reqArgs['pipeline'] = self.pipelineName
        reqArgs['job_id'] = self.jobId
        (reqArgs['email'], reqArgs['apikey'], reqArgs['url']) = self.pydasParams
        data = urllib.urlencode(reqArgs)
        request = urllib2.Request(self.proxyurl + "slicerjob/finish?" + data)
        response = urllib2.urlopen(request)
        print response

