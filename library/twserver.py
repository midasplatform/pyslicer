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
        return 'status:' + str(self.jobManager.getStatus())



class SlicerjobInit(Resource):
    isLeaf = True
    def __init__(self, jobManager):
        self.jobManager = jobManager

    def render_GET(self, request):
        print request.args
        print "SlicerjobInit"
        response = 'job:'
        if 'pipeline' in request.args and 'segmentation' in request.args['pipeline'] and 'jobid' in request.args:
             jobId = request.args['jobid'][0]#jobManager.getNextJobId()
             requestArgs = ''
             params = [(k,','.join(v)) for k,v in request.args.items()]
             params = '?'.join([k + '=' + v for k,v in params])
             print params
             print ">>>>>>>>>>>>>>>>>>>>>>TWSERVER starting SlicerProcess"
             slicerJob = SlicerProcess(jobManager, jobId, params)
             slicerJob.run() 
             response = response + str(jobId)
        return response


# check status like this:
#http://localhost:8880/slicerjob/status
# start a job like this:
#http://localhost:8880/slicerjob/init/?pipeline=segmentation&url=http://localhost/midas3&email=midas_user_email&apikey=midas_user_apikey&inputitemid=1778&coords=93.5,82.2,89.9&outputfolderid=2&outputitemname=myseg


# TODO would like to not hardcode this root dir
jobManager = SlicerProcessJobManager('/slicerweb/server')

root = ServerRoot()
slicerjobRoot = Slicerjob()
slicerjobInit = SlicerjobInit(jobManager)
slicerjobStatus = SlicerjobStatus(jobManager)

root.putChild('slicerjob', slicerjobRoot)
slicerjobRoot.putChild('init', slicerjobInit)
slicerjobRoot.putChild('status', slicerjobStatus)


reactor.listenTCP(8880, server.Site(root))
reactor.run()



# TODO create a main, allow for a diff dir
