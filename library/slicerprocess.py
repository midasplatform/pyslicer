from twisted.internet import reactor
from twisted.internet import protocol
import re
import logging
import os
import sys
import pydas
import shutil


class SlicerProcessJobManager():
    def __init__(self, tmpDirRoot, slicerPath):
        self.jobs = {}
        #self.processCount = 0
        self.tmpDirRoot = tmpDirRoot
        self.slicerPath = slicerPath
#    def getNextJobId(self):
#        # could be problematic if multithreaded
#        jobId = self.processCount
#        self.processCount = self.processCount + 1
#        self.jobs[str(jobId)] = {}
#        return jobId 
    def addJob(self, jobId):
        self.jobs[str(jobId)] = {}



    def processEvent(self, event):
        jobEvents = self.jobs[str(event.jobId)]
        jobEvents[event.eventId] = event


       
 
    def getStatus(self, jobId=None):
        print "getStatus"
        print self.jobs
        if jobId is not None and jobId in self.jobs:
            status = str(jobId) +":"+ str(sorted(self.jobs[jobId].values(), key=lambda event: int(event.eventId)))
        else:
            status = ''
            for jobId, jobEvents in self.jobs.items():
                jobEvents = sorted(jobEvents.values(), key=lambda event: int(event.eventId))
                status = status + jobId+":"+ str(jobEvents)
        return status




class SlicerProcessStatusEvent():
    statuseventpattern = 'status job=%s eventid=%s timestamp=%s eventType=%s'
    statuseventmessagepattern = statuseventpattern + ' message=%s'

    def __init__(self, jobId, eventId, timestamp, eventType, message=None):
        self.jobId = str(jobId)
        self.eventId = str(eventId)
        self.timestamp = str(timestamp)
        self.eventType = eventType
        self.message = message

    def __repr__(self):
        if self.message is not None:
            string  = self.statuseventmessagepattern % (self.jobId, self.eventId, self.timestamp, self.eventType, self.message)
        else:
            string  = self.statuseventpattern % (self.jobId, self.eventId, self.timestamp, self.eventType)
        return string

    @staticmethod
    def parseEvent(data):
        anychargroup = '(.*)'
        # first search for pattern with message as it is a superset of messageless pattern
        pattern = SlicerProcessStatusEvent.statuseventmessagepattern
        regex = pattern % tuple([anychargroup] * pattern.count('%s'))
        match = False
        m = re.search(regex, data)
        message = None
        if m is not None:
            match = True 
            #print "Match:", m.groups()
            (jobId, eventId, timestamp, eventType, message) = m.groups()
            return SlicerProcessStatusEvent(jobId, eventId, timestamp, eventType, message)
        else:
            pattern = SlicerProcessStatusEvent.statuseventpattern
            regex = pattern % tuple([anychargroup] * pattern.count('%s'))
            m = re.search(regex, data)
            if m is not None:
                match = True 
                #print "Match:", m.groups()
                (jobId, eventId, timestamp, eventType) = m.groups()
                return SlicerProcessStatusEvent(jobId, eventId, timestamp, eventType)
        return None


class SlicerPipelineStatusTracker():
    def __init__(self, pipelineName, jobId):
        self.clis = {}
        self.started = True
        self.finished = False
        self.jobId =  jobId
        self.pipelineName = pipelineName

    def reportStatus(self, event):
        # could change this to calling url if need be
        print(event)
 
    def start(self):
        self.started = True

    def finish(self):
        self.finished = True
        from __main__ import slicer
        slicer.app.exit()


class SlicerProcess(protocol.ProcessProtocol):
    def __init__(self, jobManager, jobId, requestArgs):
        self.jobManager = jobManager
        self.jobId = jobId
        self.jobManager.addJob(jobId)
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
        event = SlicerProcessStatusEvent.parseEvent(data)
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
            event = SlicerProcessStatusEvent.parseEvent(line)
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
        xvfbLogfile = os.path.join(self.jobManager.tmpDirRoot, 'xvfb.log')
        xvfbCmdParts = ['xvfb-run', '-a', '-e', xvfbLogfile]
        slicerArgs = ['--no-main-window', '--python-script']
        slicerPythonScript = ['seg_pipeline.py']
        slicerCmdParts = [self.jobManager.slicerPath] + slicerArgs + slicerPythonScript + [str(self.jobId), self.jobManager.tmpDirRoot, self.requestArgs]#['slicerjob']
        cmd = xvfbCmdParts + slicerCmdParts  
        print str(self.jobId) + " run: " + str(cmd)
        print ">>>>>>>>>>>>>>>SlicerProcess running:",str(cmd)
        reactor.spawnProcess(self, 'xvfb-run', cmd, {}, usePTY=True)





class SlicerPipeline():

    event_pipelinestart = "PipelineStart"
    event_downloadinput = "DownloadInput"
    event_process = "Process"
    event_uploadoutput = "UploadOutput"
    event_pipelineend = "PipelineEnd"
    event_exception = "Exception"

    midasstatus_started = 1
    midasstatus_done = 2
    midasstatus_exception = 3

    def __init__(self, pipelineName, jobId, pydasParams, tmpDirRoot):
        self.pipelineName = pipelineName
        self.jobId = jobId
        self.pydasParams = pydasParams
        self.tmpDirRoot = tmpDirRoot
        self.tracker = SlicerPipelineStatusTracker(pipelineName, jobId)
        self.eventIdCounter = 0
        #TODO something better with logging
        logging.basicConfig(level=logging.WARNING)
        self.log = logging.getLogger('example')

    def createTmpDir(self):
        self.tmpdirpath = ('%s_%s_tmpdir') % (self.jobId, self.pipelineName)
        # clear it out if it already exists
        if(os.path.exists(self.tmpdirpath)):
            self.removeTmpDir()
        os.mkdir(self.tmpdirpath)  
        # create a data dir
        self.datadir = os.path.join(self.tmpdirpath, 'data')
        os.mkdir(self.datadir)  
        # create an out dir
        self.outdir = os.path.join(self.tmpdirpath, 'out')
        os.mkdir(self.outdir)  
 
    def removeTmpDir(self):
        shutil.rmtree(self.tmpdirpath)


    def downloadInput(self):
        self.reportStatus(self.event_downloadinput)
        self.downloadInputImpl()        
 
    def downloadInputImpl(self):
        pass

    def downloadItem(self, itemId):
        (email, apiKey, url) = self.pydasParams
        pydas.login(email=email, api_key=apiKey, url=url)
 
        pydas._download_item(itemId, self.datadir)
        # unzip any zipped files
        for filename in os.listdir(self.datadir):
            if filename.endswith('.zip'):
                filepath = os.path.join(self.datadir, filename)
                zip = zipfile.ZipFile(filepath)
                zip.extractall(self.datadir)
                zip.close()
        # look for the header file or mha, this is very brittle
        for filename in os.listdir(self.datadir):
            if filename.endswith('.nhdr') or filename.endswith('.mha'):
                self.headerFile = os.path.join(self.datadir, filename)


    def uploadItem(self, itemName, outputFolderId):
        # read everything in the outdir and upload it as a single item
        # create a new item
        # need a folder id
        (email, apiKey, url) = self.pydasParams
        pydas.login(email=email, api_key=apiKey, url=url)
        item = pydas.communicator.create_item(pydas.token, itemName, outputFolderId)
        item_id = item['item_id']
        for filename in os.listdir(self.outdir):
            upload_token = pydas.communicator.generate_upload_token(pydas.token, item_id, filename)
            filepath=os.path.join(self.outdir, filename)
            pydas.communicator.perform_upload(upload_token, filename, itemid=item_id, filepath=filepath)
        # set the output item as an output for the job
        method = 'midas.pyslicer.add.job.output.item'
        parameters = {}
        parameters['token'] = pydas.token
        parameters['job_id'] = self.jobId
        parameters['item_id'] = item_id
        print parameters
        pydas.communicator.request(method, parameters) 
        return item_id


    def process(self):
        self.reportStatus(self.event_process)
        self.processImpl()        
 
    def processImpl(self):
        pass

    def reportStatus(self, eventType, message=None):
        eventId = self.eventIdCounter
        self.eventIdCounter = self.eventIdCounter + 1
        import time
        timestamp = time.time()
        event = SlicerProcessStatusEvent(self.jobId, eventId, timestamp, eventType, message)
        self.tracker.reportStatus(event)


    def reportProcessStatus(self, message=None):
        self.reportStatus(self.event_process, message)
    
    def uploadOutput(self):
        self.reportStatus(self.event_uploadoutput)
        self.uploadOutputImpl()        
 
    def uploadOutputImpl(self):
        pass

   
    def reportMidasStatus(self, status, condition=None):
        # TODO add these methods to pydas
        # TODO add condition to api call 
        (email, apiKey, url) = self.pydasParams
        pydas.login(email=email, api_key=apiKey, url=url)
        method = 'midas.pyslicer.update.job.status'
        parameters = {}
        parameters['token'] = pydas.token
        parameters['job_id'] = self.jobId
        parameters['status'] = status
        if condition is not None: parameters['condition'] = condition
        print parameters
        pydas.communicator.request(method, parameters) 


    def execute(self):
        try:
            self.tracker.start()
            # send pydas pipeline started
            self.reportMidasStatus(self.midasstatus_started)
            self.reportStatus(self.event_pipelinestart)
            self.createTmpDir()
            self.downloadInput()
            self.process() 
            self.uploadOutput()
            self.removeTmpDir()
            self.reportStatus(self.event_pipelineend)
            # send pydas pipeline finished
            self.reportMidasStatus(self.midasstatus_done)
            self.tracker.finish()
        except Exception as exception:
            # TODO where to do exceptions status and conditions
            # TODO send this through status tracker
            self.log.exception(exception)
            self.tracker.reportStatus(self.event_exception)
            import traceback
            etype, value, tb = sys.exc_info()
            emsg = repr(traceback.format_exception(etype, value, tb))
            self.reportMidasStatus(self.midasstatus_exception, emsg)
            exit(1)
      
