import os
import json

import vtk, slicer

from slicerjob import SlicerJob

class SlicerPdfSeg(SlicerJob):
    """This class implements a job executed in Slicer's Python environment - 
    TubeTK PDF segmentation"""
    loaded_input_volume = "Loaded Input Volume"
    loaded_label_map = "Loaded Input Label Map"
    started_segmentation = "Starting Segmentation"
    finished_segmentation = "Finished Segmentation"
    wrote_segmentation_output = "Wrote Segmentation Output"
    started_modelmaker = "Starting Modelmaker"
    finished_modelmaker = "Finished Modelmaker"
    wrote_model_output = "Wrote Model Output"

    def __init__(self, jobId, pipelineName, pydasParams, tmpDirRoot, dataDir, 
                 outDir, proxyurl, inputFile, inputLabelMap, objectId,
                 outputItemName, outputLabelMap, outputFolderId):
        SlicerJob.__init__(self, jobId, pipelineName, pydasParams, tmpDirRoot,
                           dataDir, outDir, proxyurl)
        self.inputFile = inputFile
        self.inputLabelMap = inputLabelMap
        self.objectId = map(int, objectId.split(','))
        self.outputItemName = outputItemName
        self.outputLabelMap = outputLabelMap
        self.outputFolderId = outputFolderId

    def process(self):
        """Execute TubeTK PDF segmentation """
        # Create the path to the desired output surface model file 
        outFile = self.outputItemName + '.vtp'
        outPath = os.path.join(self.outDir, outFile)
        print outPath
        # Create the path to the desired output labelmap file 
        outLabelMap = self.outputLabelMap + '.mha'
        outLabelMapPath = os.path.join(self.outDir, outLabelMap)
        print outLabelMapPath
        # Load input item and the initial labelmap
        inputPath = os.path.join(self.dataDir, self.inputFile)
        print inputPath
        (input_status, inputVolume) = slicer.util.loadVolume(inputPath, returnNode=True)
        self.report_status(self.event_process, self.loaded_input_volume)
        inputLabelMapPath = os.path.join(self.dataDir, self.inputLabelMap)
        print inputLabelMapPath
        (labelmap_status, labelMapVolume) = slicer.util.loadVolume(inputLabelMapPath, returnNode=True)
        self.report_status(self.event_process, self.loaded_label_map)
        # Set parameters for PDF segmentation
        outVolume = slicer.vtkMRMLScalarVolumeNode()
        slicer.mrmlScene.AddNode(outVolume)
        # use 0 as voidId
        voidId = 0
        params = {'inputVolume1': inputVolume.GetID(),
                  'labelmap': labelMapVolume.GetID(),
                  'outputVolume': outVolume.GetID(),
                  'voidId': voidId,
                  'reclassifyObjectMask': False,
                  'reclassifyNotObjectMask': False}
        # Get obejctId from the intial label map
        accum = vtk.vtkImageAccumulate()
        accum.SetInput(labelMapVolume.GetImageData())
        accum.UpdateWholeExtent()
        data = accum.GetOutput()
        data.Update()
        numBins = accum.GetComponentExtent()[1]
        if self.objectId:
            params["objectId"] = self.objectId
        else:
            labels = []
            for i in range(0, numBins + 1):
                numVoxels = data.GetScalarComponentAsDouble(i, 0, 0, 0)
                if (numVoxels != 0):
                    labels.append(i)
            if voidId in labels:
                labels.remove(voidId)
            params["objectId"] = labels
            print labels

        self.report_status(self.event_process, self.started_segmentation)
        # Run PDF segmentation in Slicer
        cliNode = slicer.cli.run(slicer.modules.segmentconnectedcomponentsusingparzenpdfs, None, params, wait_for_completion=True)
        self.report_status(self.event_process, self.finished_segmentation)

        # Split foreground object label from output label map
        foregroundObjectVolume = outVolume
        if self.objectId:
            thresholder = vtk.vtkImageThreshold()
            thresholder.SetNumberOfThreads(1)
            thresholder.SetInput(outVolume.GetImageData())
            thresholder.SetInValue(self.objectId[0]) # foreground label
            thresholder.SetOutValue(0)
            thresholder.ReplaceInOn()
            thresholder.ReplaceOutOn()
            thresholder.ThresholdBetween(self.objectId[0], self.objectId[0])
            thresholder.SetOutputScalarType(outVolume.GetImageData().GetScalarType())
            thresholder.Update()
            if thresholder.GetOutput().GetScalarRange() != (0.0, 0.0):
               volumesLogic = slicer.modules.volumes.logic()
               foregroundObjectVolume = volumesLogic.CreateAndAddLabelVolume(outVolume, 'foregroundLabel')
               foregroundObjectVolume.GetImageData().DeepCopy(thresholder.GetOutput())

        # Export foreground object label to local disk
        save_node_params = {'fileType': 'mha'}
        slicer.util.saveNode(foregroundObjectVolume, outLabelMapPath, save_node_params)
        self.report_status(self.event_process, self.wrote_segmentation_output)

        # Call model maker to create a surface model for foreground label only
        modelmaker = slicer.modules.modelmaker
        mhn = slicer.vtkMRMLModelHierarchyNode()
        slicer.mrmlScene.AddNode(mhn)
        parameters = {'InputVolume': outVolume.GetID(),
                      'ModelSceneFile': mhn.GetID(),
                      'FilterType': "Sinc",
                      'GenerateAll': False,
                      'StartLabel':  params["objectId"][0], # foreground label
                      'EndLabel':  params["objectId"][0], # foreground label
                      'SplitNormals': True,
                      'PointNormals': True,
                      'SkipUnNamed':  True
                      }
        self.report_status(self.event_process, self.started_modelmaker)
        cliModelNode = slicer.cli.run(modelmaker, None, parameters, wait_for_completion=True)
        self.report_status(self.event_process, self.finished_modelmaker)

        # Export output surface model to local disk
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
        reqArgs['outputlabelmap'] = self.outputLabelMap
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
            # self.log.exception(exception)
            import traceback
            etype, value, tb = sys.exc_info()
            emsg = repr(traceback.format_exception(etype, value, tb))
            print emsg
            self.report_status(self.event_exception, emsg)
            exit(1)


if __name__ == '__main__':
    (script, jobId, tmpDirRoot, json_args) = sys.argv
    arg_map = json.loads(json_args)

    pydasParams = (arg_map['email'][0], arg_map['apikey'][0], arg_map['url'][0])
    pipelineName = arg_map['pipeline'][0]
    dataDir = arg_map['data_dir'][0]
    outDir = arg_map['out_dir'][0]
    proxyurl = arg_map['proxyurl'][0]
    inputFile = arg_map['inputfile'][0]
    inputLabelMap = arg_map['inputlabelmap'][0]
    outputItemName = arg_map['outputitemname'][0]
    outputLabelMap = arg_map['outputlabelmap'][0]
    outputFolderId = arg_map['outputfolderid'][0]
    objectId = arg_map['objectid'][0]

    sp = SlicerPdfSeg(jobId, pipelineName, pydasParams, tmpDirRoot, dataDir, 
                      outDir, proxyurl, inputFile, inputLabelMap, objectId,
                      outputItemName, outputLabelMap, outputFolderId)
    sp.execute()
