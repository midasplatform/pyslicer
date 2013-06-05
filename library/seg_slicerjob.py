import os
import json

import vtk, slicer
from slicerjob import SlicerJob

class SlicerSeg(SlicerJob):
    """This class implements a job executed in Slicer's Python environment - simple region growing segmentation"""
    loaded_input_volume = "Loaded Input Volume"
    started_segmentation = "Starting Segmentation"
    finished_segmentation = "Finished Segmentation"
    started_modelmaker = "Starting Modelmaker"
    finished_modelmaker = "Finished Modelmaker"
    wrote_model_output = "Wrote Model Output"
    
    def __init__(self, jobId, pipelineName, pydasParams, tmpDirRoot, dataDir, outDir, proxyurl, inputFile, seed, outputItemName, outputFolderId):
        SlicerJob.__init__(self, jobId, pipelineName, pydasParams, tmpDirRoot, dataDir, outDir, proxyurl)
        self.inputFile = inputFile
        self.seed = seed
        self.outputItemName = outputItemName
        self.outputFolderId = outputFolderId

    def process(self):
        """Execute simple region growing segmentation """
        print "start simple region growing segmentation"
        # Take first two coords and multiply by -1
        # TODO something much more systematic dealing with coords
        (x, y, z) = [float(coord) for coord in self.seed.split(',')]
        seedPointCoords = (-1 * x, -1 * y, z)

        # Create the path to the desired output file 
        outFile = self.outputItemName + '.vtp'
        outPath = os.path.join(self.outDir, outFile)
        print outPath
        inputPath = os.path.join(self.dataDir, self.inputFile)
        print inputPath
        (status, inputVolume) = slicer.util.loadVolume(inputPath, returnNode=True)
        self.report_status(self.event_process, self.loaded_input_volume)
        # Run simple region segmentation in Slicer
        outVolume = slicer.vtkMRMLScalarVolumeNode()
        slicer.mrmlScene.AddNode(outVolume)
        fiducialNode = slicer.vtkMRMLAnnotationFiducialNode()
        fiducialNode.SetFiducialWorldCoordinates(seedPointCoords)
        fiducialNode.SetName('Seed Point')
        fiducialNode.Initialize(slicer.mrmlScene)
        fiducialsList = getNode('Fiducials List')
        params = {'inputVolume': inputVolume.GetID(), 'outputVolume': outVolume.GetID(), 'seed' : fiducialsList.GetID(), 'iterations' : 6}
        self.report_status(self.event_process, self.started_segmentation)
        cliNode = slicer.cli.run(slicer.modules.simpleregiongrowingsegmentation, None, params , wait_for_completion=True)
        self.report_status(self.event_process, self.finished_segmentation)

        # Call Slicer's model make to create a model, the only parameter is name of output file
        modelmaker = slicer.modules.modelmaker
        mhn = slicer.vtkMRMLModelHierarchyNode()
        slicer.mrmlScene.AddNode(mhn)
        parameters = {'InputVolume': outVolume.GetID(), 'ModelSceneFile': mhn.GetID()}
        self.report_status(self.event_process, self.started_modelmaker)
        cliModelNode = slicer.cli.run(modelmaker, None, parameters, wait_for_completion=True)
        self.report_status(self.event_process, self.finished_modelmaker)

        # Export the model to local disk
        # TODO change to method without memory leaks
        outputModelNode = mhn.GetNthChildNode(0).GetAssociatedNode()
        modelStorage = outputModelNode.CreateDefaultStorageNode()
        slicer.mrmlScene.AddNode(modelStorage)
        modelStorage.SetFileName(outPath)
        modelStorage.WriteData(outputModelNode)
        self.outFile = outFile
        self.report_status(self.event_process, self.wrote_model_output)

    def jobEndingNotification(self, args=None):
        """Send job ending notification to Twisted Server"""
        if args is not None:
            reqArgs = args.copy()
        else:
            reqArgs = {}
        reqArgs['outputitemname'] = self.outputItemName
        reqArgs['outputfolderid'] = self.outputFolderId
        SlicerJob.jobEndingNotification(self, reqArgs)

    def execute(self):
        """Wrapper function to execute the entire slice job"""
        try:
            self.process() 
            slicer.app.exit()
            self.jobEndingNotification()
        except StandardError as exception:
            # TODO where to do exceptions status and conditions
            #self.log.exception(exception)
            import traceback
            etype, value, tb = sys.exc_info()
            emsg = repr(traceback.format_exception(etype, value, tb))
            print emsg
            self.report_status(self.event_exception, emsg)
            exit(1)


if __name__ == '__main__':
    (script, jobId, tmpDirRoot, jsonArgs) = sys.argv
    argMap = json.loads(jsonArgs)
    pydasParams = (argMap['email'][0], argMap['apikey'][0], argMap['url'][0])

    pipelineName = argMap['pipeline'][0]
    dataDir = argMap['data_dir'][0]
    outDir = argMap['out_dir'][0]
    proxyurl = argMap['proxyurl'][0]
    inputFile = argMap['inputfile'][0]
    coords = argMap['coords'][0]
    outputItemName = argMap['outputitemname'][0]
    outputFolderId = argMap['outputfolderid'][0]

    sp = SlicerSeg(jobId, pipelineName, pydasParams, tmpDirRoot, dataDir, 
                   outDir, proxyurl, inputFile, coords, outputItemName,
                   outputFolderId)
    sp.execute()
