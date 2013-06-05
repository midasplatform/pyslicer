from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
from twisted.internet import reactor, defer
from twisted.web import server, resource

import os

from slicerprocess import SlicerProcess, SlicerProcessJobManager
from pipeline import PipelineFactory

class ServerRoot(Resource):
    """This class implements a twisted Resource Object - server root"""
    def getChild(self, name, request):
        if name == '':
            return self
        return Resource.getChild(self, name, request)

    def render_GET(self, request):
        return "Server Root, the following paths have service: slicerjob"


class Slicerjob(Resource):
    """This class implements a twisted Resource Object - /slicerjob URL segment"""
    def getChild(self, name, request):
        if name == '':
            return self
        return Resource.getChild(self, name, request)

    def render_GET(self, request):
        return "slicerjob root, the following paths have service: init, finish, reportstatus"

class SlicerjobReportStatus(Resource):
    """This class implements a twisted Resource Object - /reportstatus URL segment"""
    isLeaf = True
    
    def _report_status(self, request):
        """Callback function to report pipeline status event to the Midas server"""
        print request.args
        print "SlicerjobReportStatus"
        if 'pipeline' in request.args and 'job_id' in request.args:
            jobId = request.args['job_id'][0]
            pipelineName = request.args['pipeline'][0]
            tmpDir = os.getcwd()
            pydasParams = (request.args['email'][0], request.args['apikey'][0], request.args['url'][0])
            pipelinefactory = PipelineFactory()
            pipeline = pipelinefactory.getPipeline(pipelineName, jobId, pydasParams, tmpDir, request.args)
            pipeline.get_events()
            if 'message'in request.args:
                pipeline.reportStatus(request.args['event_type'][0], request.args['message'][0])
                request.write("\nreport job status:" + str(request.args['event_type'][0]) + str(request.args['message'][0]))
            else:
                pipeline.reportStatus(request.args['event_type'][0])
                request.write("\nreport job status:" + str(request.args['event_type'][0]))
            request.finish()
        else:
            request.finish()

    def render_GET(self, request):
        """Handle report job status request asynchronously """
        reactor.callLater(0, self._report_status, request)
        return NOT_DONE_YET

class SlicerjobInit(Resource):
    """This class implements a twisted Resource Object - /init URL segment"""
    isLeaf = True
    def __init__(self, jobManager):
        self.jobManager = jobManager
    
    def _download_process(self, request):
        """Callback function to download input file(s) from the Midas server, 
        and then start the slicer job"""
        print request.args
        print "SlicerjobInit download"
        request.write('init job')
        if 'pipeline' in request.args and 'job_id' in request.args:
            jobId = request.args['job_id'][0]
            pipelineName = request.args['pipeline'][0]
            print ">>>>>>>>>>>>>>>>>>>>>>TWSERVER starting SlicerProcess"
            tmpDir = os.getcwd()
            pydasParams = (request.args['email'][0], request.args['apikey'][0], request.args['url'][0])
            print pydasParams
            request.write("\nstarted job " + str(jobId))
            request.write("\nstarted downloading item(s)")
            # Call pipeline's executeDownload function to do the real download
            pipelinefactory = PipelineFactory()
            pipeline = pipelinefactory.getPipeline(pipelineName, jobId, pydasParams, tmpDir, request.args)
            (self.dataDir, self.outDir, self.inputfiles) = pipeline.executeDownload()
            request.write("\nfinished downloading item(s)")
            request.args['proxyurl'] = [self.jobManager.proxyurl]
            request.args['data_dir'] = [self.dataDir]
            request.args['out_dir'] = [self.outDir]
            # Add the input files into the parameters
            for k, v in self.inputfiles.items():
                request.args[k] = [v]
            request.write("\nstarted processing item(s) ")
            # Create a new process for the Slicer job asynchronously
            slicerJob = SlicerProcess(self.jobManager, jobId, pipelineName, request.args)
            d = defer.Deferred()
            reactor.callLater(0, d.callback, None)
            d.addCallback(lambda ignored: slicerJob.run())
            request.finish()
        else:
            request.finish()

    def render_GET(self, request):
        """Handle job init request asynchronously"""
        reactor.callLater(0, self._download_process, request)
        return NOT_DONE_YET


class SlicerjobFinish(Resource):
    """This class implements a twisted Resource Object - /finish URL segment"""
    isLeaf = True

    def _upload(self, request):
        """Callback function to upload output file(s) to the Midas server, 
        and then start the slicer job"""
        print request.args
        print "SlicerjobFinish"
        request.write('Upload output')
        if 'pipeline' in request.args and 'job_id' in request.args:
             jobId = request.args['job_id'][0]
             pipelineName = request.args['pipeline'][0]
             print ">>>>>>>>>>>>>>>>>>>>>>TWSERVER finishing SlicerProcess"
             tmpDir = os.getcwd()
             pydasParams = (request.args['email'][0], request.args['apikey'][0], request.args['url'][0])
             response = "\nstarted uploading output item"
             # Call pipeline's executeUpload function to do the real upload
             pipelinefactory = PipelineFactory()
             pipeline = pipelinefactory.getPipeline(pipelineName, jobId, pydasParams, tmpDir, request.args)
             pipeline.executeUpload()
             request.write("\nfinished uploading output item")
             request.write("\nfinished job " + str(jobId))
             request.finish()
        else:
            request.finish()
    
    def render_GET(self, request):
        """Handle job ennding request asynchronously"""
        reactor.callLater(0, self._upload, request)
        return NOT_DONE_YET

# check status like this:
#http://localhost:8880/slicerjob/status/?jobid=122
# start a job like this:
#http://localhost:8880/slicerjob/init/?pipeline=segmentation&url=http://localhost/midas3&email=midas_user_email&apikey=midas_user_apikey&inputitemid=1778&coords=93.5,82.2,89.9&outputfolderid=2&outputitemname=myseg


if __name__ == '__main__':
    # read the config file for slicer_path
    config = {}
    with open('twserver.cfg') as config_file:
        for line in config_file.readlines():
            line = line.strip()
            if line is not None and line != '':
                cols = line.split('=')
                config[cols[0]] = cols[1]
    if 'slicer_path' not in config or not os.path.isfile(config['slicer_path']):
        print "You must specify the path to the Slicer exe as slicer_path in twserver.cfg"
        exit(1)
    if 'proxy_url' not in config:
        print "You must specify the Slicer Proxy Server URL"
        exit(1)
    # Set current directory as temporary working directory
    jobManager = SlicerProcessJobManager(os.getcwd(), config['slicer_path'], config['proxy_url'])
    root = ServerRoot()
    slicerjobRoot = Slicerjob()
    slicerjobInit = SlicerjobInit(jobManager)
    slicerjobFinish = SlicerjobFinish()
    slicerjobReportStatus = SlicerjobReportStatus()
    root.putChild('slicerjob', slicerjobRoot)
    slicerjobRoot.putChild('init', slicerjobInit)
    slicerjobRoot.putChild('finish', slicerjobFinish)
    slicerjobRoot.putChild('reportstatus', slicerjobReportStatus)
    # Start Twisted server
    reactor.listenTCP(8880, server.Site(root))
    reactor.run()
