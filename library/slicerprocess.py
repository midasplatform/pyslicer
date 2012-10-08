# TODO this is a terrible HACK to add site packages to the Slicer Python
# but better than what was before, hopefully to be improved further
tmp_paths = ['/usr/lib/python2.6/dist-packages/',
             '/usr/local/lib/python2.6/dist-packages/']
import sys
sys.path.extend(tmp_paths)

from twisted.internet import reactor
from twisted.internet import protocol
import re
import logging
import os
import sys
import pydas
import shutil
import json

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




class SlicerProcessStatusEvent():
    statuseventpattern = 'status&remoteprocessing_job_id=%s&event_id=%s&timestamp=%s&event_type=%s'
    statuseventmessagepattern = statuseventpattern + '&message=%s'

    def __init__(self, jobId, eventId, timestamp, eventType, message=None):
        self.jobId = str(jobId)
        self.eventId = str(eventId)
        self.timestamp = str(timestamp)
        self.eventType = eventType
        self.message = message
        self.jobstatus_id = None

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
    pipeline_scripts = {'segmentation' : 'seg_pipeline.py', 'registration' : 'reg_pipeline.py'}



    def __init__(self, jobManager, jobId, pipeline, request_args):
    #def __init__(self, jobManager, jobId, requestArgs, jsonargs):
        self.jobManager = jobManager
        self.jobId = jobId
        self.jobManager.addJob(jobId)
        #self.requestArgs = requestArgs
        self.pipeline = pipeline
        self.request_args = request_args
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
        slicerPythonScript = [self.pipeline_scripts[self.pipeline]]
        #licerPythonScript = ['seg_pipeline.py']
        import json
        json_args = json.dumps(self.request_args)
        print json_args
        print [json_args]
        print [str(self.jobId), self.jobManager.tmpDirRoot, json_args]
        slicerCmdParts = [self.jobManager.slicerPath] + slicerArgs + slicerPythonScript + [str(self.jobId), self.jobManager.tmpDirRoot, json_args]#['slicerjob']
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
        self.register_events()

    def create_event(self, event_type, message=None):
        event_id = self.eventIdCounter
        self.eventIdCounter = self.eventIdCounter + 1
        timestamp = 0
        event = SlicerProcessStatusEvent(self.jobId, event_id, timestamp, event_type, message)
        return event

    def create_process_event(self, message):
        return self.create_event(self.event_process, message)

    def define_events(self):
        self.events_map = {}
        events = [self.create_event(event_type) for event_type in [self.event_pipelinestart, self.event_downloadinput]]
        events = events + self.define_process_events()
        events = events + [self.create_event(event_type) for event_type in [self.event_uploadoutput, self.event_pipelineend]]
        for event in events:
            self.events_map[event.eventId] = event
        # then when it is their time to nofify, call notify passing in jobstatu_id and timestamp
        # need an imple method for subclasses to list their process events
        # maybe a map of event types to event, then a submap for process events?
        # somehow i need to keep up with all these events here
        # and maybe there is no reason to print them in the tracker anymore 

    def register_events(self):
        # get all the events, register them with the midas server
        self.define_events()
        events = self.events_map.values()
        method = 'midas.pyslicer.add.jobstatuses'
        parameters = {}
        json_events = json.dumps([str(event) for event in events])
        print json_events
        (email, apiKey, url) = self.pydasParams
        pydas.login(email=email, api_key=apiKey, url=url)
        parameters['token'] = pydas.token
        parameters['events'] = json_events
        event_id_to_jobstatus_id = pydas.communicator.request(method, parameters) 
        for (event_id, jobstatus_id) in event_id_to_jobstatus_id.items():
            event = self.events_map[event_id]
            event.jobstatus_id = jobstatus_id



    def define_process_events(self):
        # should be overwritten in the subclass
        return []

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
        # return the path to the name of the item
        item = pydas.communicator.item_get(pydas.token, itemId)
        return os.path.join(self.datadir, item['name'])


    def uploadItem(self, itemName, outputFolderId, out_file=None, item_description=None):
        # read everything in the outdir and upload it as a single item
        # create a new item
        # need a folder id
        (email, apiKey, url) = self.pydasParams
        pydas.login(email=email, api_key=apiKey, url=url)
        if item_description is not None:
            item = pydas.communicator.create_item(pydas.token, itemName, outputFolderId, description=item_description)
        else:
            item = pydas.communicator.create_item(pydas.token, itemName, outputFolderId)
        item_id = item['item_id']
        if out_file is not None:
            # only upload this one file
            upload_token = pydas.communicator.generate_upload_token(pydas.token, item_id, out_file)
            filepath=os.path.join(self.outdir, out_file)
            pydas.communicator.perform_upload(upload_token, out_file, itemid=item_id, filepath=filepath)
        else:
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
        self.processImpl()        
 
    def processImpl(self):
        pass

    def reportStatus(self, eventType, message=None):
        # find the event
        match = None
        for event in self.events_map.values():
            if event.eventType == eventType and event.message == message:
                match = event
        if match is None:
            print 'reportStatus',    eventType, message
            print "NO MATCH"
            exit(1)
        import time
        timestamp = time.time()
        match.timestamp = timestamp
        method = 'midas.pyslicer.notify.jobstatus'
        parameters = {}
        parameters['token'] = pydas.token
        parameters['jobstatus_id'] = match.jobstatus_id
        parameters['notify_date'] = timestamp
        pydas.communicator.request(method, parameters) 


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
        method = 'midas.pyslicer.update.job'
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
      

