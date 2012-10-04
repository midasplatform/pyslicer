from twisted.internet.task import deferLater
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
from twisted.internet import reactor
from twisted.web import server, resource




#TODO clean imports

from slicerprocess import SlicerProcess, SlicerProcessJobManager

class ServerRoot(Resource):
    def getChild(self, name, request):
        if name == '':
            return self
        return Resource.getChild(self, name, request)

    def render_GET(self, request):
        return "Server Root, the following paths have service: slicerjob, status"


class Slicerjob(Resource):
    def getChild(self, name, request):
        if name == '':
            return self
        return Resource.getChild(self, name, request)

    def render_GET(self, request):
        return "slicerjob root, the following paths have service: init, status"

class SlicerjobStatus(Resource):
    isLeaf = True
    def __init__(self, jobManager):
        self.jobManager = jobManager

    def render_GET(self, request):
        if 'job_id' in request.args:
            return str(self.jobManager.getStatus(jobId=request.args['jobid'][0]))
        else:
            return str(self.jobManager.getStatus())



class SlicerjobInit(Resource):
    isLeaf = True
    def __init__(self, jobManager):
        self.jobManager = jobManager

    def render_GET(self, request):
        print request.args
        print "SlicerjobInit"
        response = 'job:'
        if 'pipeline' in request.args and 'job_id' in request.args:
             print "YES"
             job_id = request.args['job_id'][0]
             pipeline = request.args['pipeline'][0]
             print ">>>>>>>>>>>>>>>>>>>>>>TWSERVER starting SlicerProcess"
             slicerJob = SlicerProcess(jobManager, job_id, pipeline, request.args)
             slicerJob.run() 
             response = "started job " + str(job_id)
        return response


# check status like this:
#http://localhost:8880/slicerjob/status/?jobid=122
# start a job like this:
#http://localhost:8880/slicerjob/init/?pipeline=segmentation&url=http://localhost/midas3&email=midas_user_email&apikey=midas_user_apikey&inputitemid=1778&coords=93.5,82.2,89.9&outputfolderid=2&outputitemname=myseg


if __name__ == '__main__':
    # read the config file for slicer_path
    config_file = open('twserver.cfg')
    config = {}
    for line in config_file:
        line = line.strip()
        if line is not None and line != '':
            cols = line.split('=')
            config[cols[0]] = cols[1]
    config_file.close()
    import os
    if 'slicer_path' not in config or not os.path.isfile(config['slicer_path']):
        print "You must specify the path to the Slicer exe as slicer_path in twserver.cfg"
        exit(1)
    # set current dir as temp working dir
    jobManager = SlicerProcessJobManager(os.getcwd(), config['slicer_path'])
    root = ServerRoot()
    slicerjobRoot = Slicerjob()
    slicerjobInit = SlicerjobInit(jobManager)
    slicerjobStatus = SlicerjobStatus(jobManager)
    root.putChild('slicerjob', slicerjobRoot)
    slicerjobRoot.putChild('init', slicerjobInit)
    slicerjobRoot.putChild('status', slicerjobStatus)
    reactor.listenTCP(8880, server.Site(root))
    reactor.run()
