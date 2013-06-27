import re
import logging
import os
import sys
import shutil
import json

import pydas

class PipelineStatusEvent():
    """This class implements pipeline status events."""
    statuseventpattern = 'status&remoteprocessing_job_id=%s&event_id=%s&timestamp=%s&event_type=%s'
    statuseventmessagepattern = statuseventpattern + '&message=%s'

    def __init__(self, jobId, eventId, timestamp, eventType, message=None):
        self.jobId = str(jobId)
        self.eventId = str(eventId)
        self.timestamp = str(timestamp)
        self.eventType = eventType
        self.message = message
        self.jobstatusId = None

    def __repr__(self):
        if self.message is not None:
            string = self.statuseventmessagepattern % (self.jobId, self.eventId,
                self.timestamp, self.eventType, self.message)
        else:
            string = self.statuseventpattern % (self.jobId, self.eventId,
                self.timestamp, self.eventType)
        return string

    @staticmethod
    def parseEvent(data):
        """Create a status event if the input data matches status event pattern"""
        anychargroup = '(.*)'
        # first search for pattern with message as it is a superset of messageless pattern
        pattern = PipelineStatusEvent.statuseventmessagepattern
        regex = pattern % tuple([anychargroup] * pattern.count('%s'))
        match = False
        m = re.search(regex, data)
        message = None
        if m is not None:
            match = True
            (jobId, eventId, timestamp, eventType, message) = m.groups()
            return PipelineStatusEvent(jobId, eventId, timestamp, eventType, message)
        else:
            pattern = PipelineStatusEvent.statuseventpattern
            regex = pattern % tuple([anychargroup] * pattern.count('%s'))
            m = re.search(regex, data)
            if m is not None:
                match = True
                (jobId, eventId, timestamp, eventType) = m.groups()
                return PipelineStatusEvent(jobId, eventId, timestamp, eventType)
        return None


class PipelineFactory():
    """This class implements an interface to get pipeline and the python script
    running within Slicer."""
    def getPipeline(self, pipelineName, jobId, pydasParams, tmpDirRoot, args):
        """Return a specific pipeline based on input parameters"""
        if pipelineName == 'segmentation':
            return SegPipeline(pipelineName, jobId, pydasParams, tmpDirRoot, args)
        elif pipelineName == 'registration':
            return RegPipeline(pipelineName, jobId, pydasParams, tmpDirRoot, args)
        elif pipelineName == 'pdfsegmentation':
            return PdfSegPipeline(pipelineName, jobId, pydasParams, tmpDirRoot, args)

        else:
            return None

    def getSlicerScript(self, pipelineName):
        """Return the name of a python script running within Slicer's python 
        environment."""
        if pipelineName == 'segmentation':
            return 'seg_slicerjob.py'
        elif pipelineName == 'registration':
            return 'reg_slicerjob.py'
        elif pipelineName == 'pdfsegmentation':
            return 'pdfseg_slicerjob.py'
        else:
            return None


class Pipeline():
    """This class implements the base class for Pyslicer's pipelines."""
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
        self.eventIdCounter = 0
        # TODO something better with logging
        logging.basicConfig(level=logging.WARNING)
        self.log = logging.getLogger('example')

    def create_event(self, eventType, message=None):
        """Create a pipeline status event"""
        eventId = self.eventIdCounter
        self.eventIdCounter = self.eventIdCounter + 1
        timestamp = 0
        event = PipelineStatusEvent(self.jobId, eventId, timestamp, eventType, message)
        return event

    def create_process_event(self, message):
        return self.create_event(self.event_process, message)

    def define_events(self):
        """Define all the status events for this pipeline"""
        self.eventsMap = {}
        events = [self.create_event(eventType)
            for eventType in [self.event_pipelinestart, self.event_downloadinput]]
        events = events + self.define_process_events()
        events = events + [self.create_event(eventType)
            for eventType in [self.event_uploadoutput, self.event_pipelineend]]
        for event in events:
            self.eventsMap[event.eventId] = event
        # Keep original comments as below
        # then when it is their time to nofify, call notify passing in jobstatu_id and timestamp
        # need an imple method for subclasses to list their process events
        # maybe a map of event types to event, then a submap for process events?
        # somehow i need to keep up with all these events here
        # and maybe there is no reason to print them in the tracker anymore 

    def register_events(self):
        """"Get all the status events of this pipeline, register them with the
        Midas server"""
        self.define_events()
        events = self.eventsMap.values()
        method = 'midas.pyslicer.add.jobstatuses'
        parameters = {}
        jsonEvents = json.dumps([str(event) for event in events])
        print jsonEvents
        (email, apiKey, url) = self.pydasParams
        pydas.login(email=email, api_key=apiKey, url=url)
        parameters['token'] = pydas.session.token
        parameters['events'] = jsonEvents
        eventId_to_jobstatusId = pydas.session.communicator.request(method, parameters) 
        for (eventId, jobstatusId) in eventId_to_jobstatusId.items():
            event = self.eventsMap[eventId]
            event.jobstatusId = jobstatusId

    def get_events(self):
        """Get all the registered status events for a given pipeline job"""
        self.define_events()
        method = 'midas.pyslicer.get.job.status'
        parameters = {}
        (email, apiKey, url) = self.pydasParams
        pydas.login(email=email, api_key=apiKey, url=url)
        parameters['token'] = pydas.session.token
        parameters['job_id'] = self.jobId
        parameters['status_only'] = True
        eventId_to_jobstatusId = pydas.session.communicator.request(method, parameters)
        jobstatuses = pydas.session.communicator.request(method, parameters)
        for jobstatus in jobstatuses:
            event = self.eventsMap[jobstatus['event_id']]
            event.jobstatusId = jobstatus['jobstatus_id']

    def define_process_events(self):
        """Define the process events for a pipeline. It should be overwritten
        in the subclass"""
        return []

    def createTmpDir(self):
        """Create a temporary directory for a pipeline job"""
        self.tmpdirpath = ('%s_%s_tmpdir') % (self.jobId, self.pipelineName)
        # clear it out if it already exists
        if(os.path.exists(self.tmpdirpath)):
            self.removeTmpDir()
        os.mkdir(self.tmpdirpath)  
        # create a directory for input data
        self.dataDir = os.path.join(self.tmpdirpath, 'data')
        os.mkdir(self.dataDir)  
        # create a directory for output results
        self.outDir = os.path.join(self.tmpdirpath, 'out')
        os.mkdir(self.outDir)  

    def downloadInput(self):
        """Report download input event and then call the actual download function"""
        self.reportStatus(self.event_downloadinput)
        self.downloadInputImpl()        

    def downloadInputImpl(self):
        """Download one input file. It should be overwritten by subclasses if 
        they need more input data"""
        self.tempfiles = {}
        self.tempfiles['inputfile'] = self.downloadItem(self.itemId)
        print self.tempfiles

    def downloadItem(self, itemId):
        """Download a single item from the Midas server using pydas"""
        (email, apiKey, url) = self.pydasParams
        pydas.login(email=email, api_key=apiKey, url=url)
        pydas.api._download_item(itemId, self.dataDir)
        # Unzip any zipped files
        for filename in os.listdir(self.dataDir):
            if filename.endswith('.zip'):
                filepath = os.path.join(self.dataDir, filename)
                zip = zipfile.ZipFile(filepath)
                zip.extractall(self.dataDir)
                zip.close()
        # Return the path to the name of the item
        item = pydas.session.communicator.item_get(pydas.session.token, itemId)
        return item['name']

    def executeDownload(self):
        """Register a pipeline's events, start the pipeline as a Midas job, 
        create the temporary directory for this job, and then download 
        the input file(s)"""
        try:
            self.register_events()
            # Send pydas pipeline started event
            self.reportMidasStatus(self.midasstatus_started)
            self.reportStatus(self.event_pipelinestart)
            self.createTmpDir()
            self.downloadInput()
            return (self.dataDir, self.outDir, self.tempfiles)
        except StandardError as exception:
            # TODO where to do exceptions status and conditions
            self.log.exception(exception)
            print self.event_exception
            import traceback
            etype, value, tb = sys.exc_info()
            emsg = repr(traceback.format_exception(etype, value, tb))
            self.reportMidasStatus(self.midasstatus_exception, emsg)
            exit(1)

    def setTmpDir(self):
        """Set temporary directory"""
        self.tmpdirpath = ('%s_%s_tmpdir') % (self.jobId, self.pipelineName)
        self.dataDir = os.path.join(self.tmpdirpath, 'data')
        self.outDir = os.path.join(self.tmpdirpath, 'out')
        
    def uploadItem(self, itemName, outputFolderId, srcDir=None, outFile=None,
                   itemDescription=None, type=None):
        """Read everything in the srcDir and upload it as a single item. If 
        outFile is set, only upload that file"""
        (email, apiKey, url) = self.pydasParams
        pydas.login(email=email, api_key=apiKey, url=url)
        # Create a new item (fold_id is required)
        if itemDescription is not None:
            item = pydas.session.communicator.create_item(pydas.session.token,
                itemName, outputFolderId, description=itemDescription)
        else:
            item = pydas.session.communicator.create_item(pydas.session.token,
                itemName, outputFolderId)
        itemId = item['item_id']
        if srcDir is None:
            srcDir = self.outDir
        if outFile is not None:
            # Only upload this one file
            uploadToken = pydas.session.communicator.generate_upload_token(
                pydas.session.token, itemId, outFile)
            filepath = os.path.join(srcDir, outFile)
            pydas.session.communicator.perform_upload(uploadToken, outFile,
                itemid=itemId, filepath=filepath)
        else:
            for filename in os.listdir(srcDir):
                uploadToken = pydas.session.communicator.generate_upload_token(
                    pydas.session.token, itemId, filename)
                filepath = os.path.join(srcDir, filename)
                pydas.session.communicator.perform_upload(uploadToken, filename,
                    itemid=itemId, filepath=filepath)
        # Set the output item as an output for the job
        method = 'midas.pyslicer.add.job.output.item'
        parameters = {}
        parameters['token'] = pydas.session.token
        parameters['job_id'] = self.jobId
        parameters['item_id'] = itemId
        if type is not None:
            parameters['type'] = type
        print parameters
        pydas.session.communicator.request(method, parameters) 
        return itemId

    def uploadOutput(self):
        """Report upload output event and then call the actual upload function"""
        self.reportStatus(self.event_uploadoutput)
        self.uploadOutputImpl()        

    def uploadOutputImpl(self):
        """Upload output file(s) of the pipeline job. It should be overwritten
        by subclasses"""
        pass

    def executeUpload(self):
        """Get registered events for this pipeline, get the temporary directory
        for this job, upload the output file(s), delete the temporary directory,
        and then end the pipeline"""
        try:
            self.get_events()
            self.setTmpDir()
            self.uploadOutput()
            self.removeTmpDir()
            self.reportStatus(self.event_pipelineend)
            # Send pydas pipeline finished event
            self.reportMidasStatus(self.midasstatus_done)
        except StandardError as exception:
            # TODO where to do exceptions status and conditions
            self.log.exception(exception)
            print self.event_exception
            import traceback
            etype, value, tb = sys.exc_info()
            emsg = repr(traceback.format_exception(etype, value, tb))
            self.reportMidasStatus(self.midasstatus_exception, emsg)
            exit(1)

    def removeTmpDir(self):
        """delete the temporary directory and its sub-directories and files"""
        shutil.rmtree(self.tmpdirpath)

    def reportProcessStatus(self, message=None):
        self.reportStatus(self.event_process, message)

    def reportStatus(self, eventType, message=None):
        """Report event status to the Midas server"""
        # Find the event
        match = None
        for event in self.eventsMap.values():
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
        parameters['token'] = pydas.session.token
        parameters['jobstatus_id'] = match.jobstatusId
        parameters['notify_date'] = timestamp
        pydas.session.communicator.request(method, parameters) 

    def reportMidasStatus(self, status, condition=None):
        """Report the pipeline job status (started, done, exception) to the 
        Midas server"""
        # TODO add these methods to pydas
        # TODO add condition to api call 
        (email, apiKey, url) = self.pydasParams
        pydas.login(email=email, api_key=apiKey, url=url)
        method = 'midas.pyslicer.update.job'
        parameters = {}
        parameters['token'] = pydas.session.token
        parameters['job_id'] = self.jobId
        parameters['status'] = status
        if condition is not None: parameters['condition'] = condition
        print parameters
        pydas.session.communicator.request(method, parameters) 


class SegPipeline(Pipeline):
    """This class implements a pipeline for simple region growing segmentation."""
    loaded_input_volume = "Loaded Input Volume"
    started_segmentation = "Starting Segmentation"
    finished_segmentation = "Finished Segmentation"
    started_modelmaker = "Starting Modelmaker"
    finished_modelmaker = "Finished Modelmaker"
    wrote_model_output = "Wrote Model Output"

    def __init__(self, pipelineName, jobId, pydasParams, tmpDirRoot, jsonArgs):
        Pipeline.__init__(self, pipelineName, jobId, pydasParams, tmpDirRoot)
        print jsonArgs
        if 'inputitemid' in jsonArgs:
            self.itemId = jsonArgs['inputitemid'][0]
        if 'outputitemname' in jsonArgs:
            self.outputItemName = jsonArgs['outputitemname'][0]
            self.outputFolderId = jsonArgs['outputfolderid'][0]

    def define_process_events(self):
        """Define the process events for simple region growing segmentation."""
        process_events = [self.loaded_input_volume, self.started_segmentation,
            self.finished_segmentation, self.started_modelmaker,
            self.finished_modelmaker, self.wrote_model_output]
        process_events = [self.create_process_event(eventType) for eventType in process_events]
        print process_events
        return process_events

    def uploadOutputImpl(self):
        """Upload output item (surface model) to the Midas server."""
        self.outFile = self.outputItemName + '.vtp'
        itemId = self.uploadItem(self.outFile, self.outputFolderId)
        (email, apiKey, url) = self.pydasParams
        pydas.login(email=email, api_key=apiKey, url=url)
        # TODO move metadata to superclass
        # Set metadata on the output item
        method = 'midas.item.setmultiplemetadata'
        parameters = {}
        parameters['token'] = pydas.session.token
        parameters['itemid'] = itemId
        parameters['count'] = 2
        # Use red to display the input seed and the contour of the output 
        # surface model in ParaView
        parameters['element_1'] = 'ParaView'
        parameters['qualifier_1'] = 'DiffuseColor'
        parameters['value_1'] = '[1.0,0.0,0.0]'
        # In ParaView, use [180, 180, 0] orientation to display the surface model 
        # which is generated by Slicer's model maker
        # TODO: make sure this hard-coded orientation on the ModelMaker output
        # is always correct
        parameters['element_2'] = 'ParaView'
        parameters['qualifier_2'] = 'Orientation'
        parameters['value_2'] = '[180.0,180.0,0.0]'
        print parameters
        pydas.session.communicator.request(method, parameters)


class RegPipeline(Pipeline):
    """This class implements a pipeline for simple region growing registration."""
    loaded_input_volumes = "Loaded Input Volumes"
    finished_registration = "Finished Registration"
    wrote_transformed_volume = "Wrote Transformed Volume"
    wrote_transform = "Wrote Transform"

    def __init__(self, pipelineName, jobId, pydasParams, tmpDirRoot, jsonArgs):
        Pipeline.__init__(self, pipelineName, jobId, pydasParams, tmpDirRoot)
        print jsonArgs
        if 'fixed_item_id' in jsonArgs:
            self.fixedItemId = jsonArgs['fixed_item_id'][0]
            self.movingItemId = jsonArgs['moving_item_id'][0]
            self.fixedFiducialsList = json.loads(argMap['fixed_fiducials'][0])
            self.movingFiducialsList = json.loads(argMap['moving_fiducials'][0])
            self.transformType = jsonArgs['transformType'][0]
        if 'output_folder_id' in jsonArgs:
            self.outputFolderId = jsonArgs['output_folder_id'][0]
            self.outputVolumeName = jsonArgs['output_volume_name'][0]
            self.outputTransformName = jsonArgs['output_transform_name'][0]

    def define_process_events(self):
        """Define the process events for simple region growing registration."""
        process_events = [self.loaded_input_volumes, self.finished_registration, self.wrote_transformed_volume, self.wrote_transform]
        process_events = [self.create_process_event(eventType) for eventType in process_events]
        print process_events
        return process_events

    def downloadInputImpl(self):
        """Download input items."""
        self.tempfiles = {}
        self.tempfiles['fixed_volume_file'] = self.downloadItem(self.fixedItemId)
        self.tempfiles['moving_volume_file'] = self.downloadItem(self.movingItemId)
        print self.tempfiles

    def uploadOutputImpl(self):
        """Upload output items to the Midas server."""
        (email, apiKey, url) = self.pydasParams
        pydas.login(email=email, api_key=apiKey, url=url)
        folder = pydas.session.communicator.create_folder(pydas.session.token, 'output_'+self.jobId, self.outputFolderId)
        folderId = folder['folder_id']
        itemId = self.uploadItem(self.outputVolumeName, folderId, self.transformed_volume, itemDescription='output volume')
        itemId = self.uploadItem(self.outputTransformName, folderId, self.transform, itemDescription='output transform')


class PdfSegPipeline(Pipeline):
    """This class implements a pipeline for TubeTK PDF segmentation."""
    loaded_input_volume = "Loaded Input Volume"
    loaded_label_map = "Loaded Input Label Map"
    started_segmentation = "Starting Segmentation"
    finished_segmentation = "Finished Segmentation"
    wrote_segmentation_output = "Wrote Segmentation Output"
    started_modelmaker = "Starting Modelmaker"
    finished_modelmaker = "Finished Modelmaker"
    wrote_model_output = "Wrote Model Output"

    def __init__(self, pipelineName, jobId, pydasParams, tmpDirRoot, json_args):
        Pipeline.__init__(self, pipelineName, jobId, pydasParams, tmpDirRoot)
        print json_args
        if 'inputitemid' in json_args:
            self.itemId = json_args['inputitemid'][0]
            self.labelMapItemId = json_args['inputlabelmapid'][0]
        if 'outputitemname' in json_args:
            self.outputItemName = json_args['outputitemname'][0]
            self.outputLabelMap = json_args['outputlabelmap'][0]
            self.outputFolderId = json_args['outputfolderid'][0]
        if 'presetitemid' in json_args:
            self.presetItemId = json_args['presetitemid'][0]
        else:
            self.presetItemId = None

    def define_process_events(self):
        """Define the process events for TubeTK PDF segmentation."""
        process_events = [self.loaded_input_volume, self.loaded_label_map, 
            self.started_segmentation, self.finished_segmentation,
            self.wrote_segmentation_output, self.started_modelmaker,
            self.finished_modelmaker, self.wrote_model_output]
        process_events = [self.create_process_event(event_type) for event_type in process_events]
        print process_events
        return process_events

    def downloadInputImpl(self):
        """Download input item and initial label map from the Midas server."""
        self.tempfiles = {}
        self.tempfiles['inputfile'] = self.downloadItem(self.itemId)
        # In case user saves initial label map with the same name multiple times
        itemName = self.downloadItem(self.labelMapItemId)
        bitstreamName = os.path.splitext(itemName)[0] + '.mha'
        self.tempfiles['inputlabelmap'] = bitstreamName
        if not self.presetItemId is None:
            self.tempfiles['presetfile'] = self.downloadItem(self.presetItemId)
        print self.tempfiles

    def uploadOutputImpl(self):
        """Upload output labelmap and its surface model to the Midas server."""
        # Upload output labelmap file (its type is 'labelmap')
        self.outLabelMapFile =  self.outputLabelMap + '.mha'
        os.mkdir(os.path.join(self.outDir, "labelmap"))
        labelMapTmpDir = os.path.join(self.outDir, "labelmap")
        shutil.copy(os.path.join(self.outDir, self.outLabelMapFile), labelMapTmpDir)
        labelmapItemId = self.uploadItem(self.outLabelMapFile, self.outputFolderId, srcDir=labelMapTmpDir, type='labelmap')
        # Upload outpuf surface model file (default type)
        self.outFile = self.outputItemName + '.vtp'
        os.mkdir(os.path.join(self.outDir, "outfile"))
        outFileTmpDir = os.path.join(self.outDir, "outfile")
        shutil.copy(os.path.join(self.outDir, self.outFile), outFileTmpDir)
        itemId = self.uploadItem(self.outFile, self.outputFolderId, srcDir=outFileTmpDir)
        (email, apiKey, url) = self.pydasParams
        pydas.login(email=email, api_key=apiKey, url=url)
        # Set metadata on the output item
        method = 'midas.item.setmultiplemetadata'
        parameters = {}
        parameters['token'] = pydas.session.token
        parameters['itemid'] = itemId
        parameters['count'] = 2
        # Use red to display the input seed and the contour of the output 
        # surface model in ParaView
        parameters['element_1'] = 'ParaView'
        parameters['qualifier_1'] = 'DiffuseColor'
        parameters['value_1'] = '[1.0,0.0,0.0]'
        # In ParaView, use [180, 180, 0] orientation to display the surface model 
        # which is generated by Slicer's model maker
        parameters['element_2'] = 'ParaView'
        parameters['qualifier_2'] = 'Orientation'
        parameters['value_2'] = '[180.0,180.0,0.0]'
        print parameters
        pydas.session.communicator.request(method, parameters)
