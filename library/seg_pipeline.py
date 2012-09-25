from __main__ import vtk, slicer


from slicerprocess import SlicerPipeline

class SlicerSegPipeline(SlicerPipeline):

    def __init__(self, jobId, pydasParams, tmpDirRoot, itemId, seed, outputItemName, outputFolderId ):
        SlicerPipeline.__init__(self, 'segmentationmodel', jobId, pydasParams, tmpDirRoot)
        self.itemId = itemId
        self.seed = seed
        self.outputItemName = outputItemName
        self.outputFolderId = outputFolderId

    def downloadInputImpl(self):
        #print "segmodeldownloadinputimpl"
        self.downloadItem(self.itemId)
   
    def processImpl(self):
        #print "segmodelprocessimpl"
        # take first two coords and multiply by -1
        # TODO something much more systematic dealing with coords
        (x, y, z) = [float(coord) for coord in self.seed.split(',')]
        seedPointCoords = (-1 * x, -1 * y, z)
  
        # create the path to the desired output file 
        outFile = self.outputItemName + '.vtp'
        outPath = os.path.join(self.outdir, outFile)

        (status, inputVolume) = slicer.util.loadVolume(self.headerFile, returnNode=True)
        self.reportProcessStatus("Loaded Input Volume")

        outVolume = slicer.vtkMRMLScalarVolumeNode()
        slicer.mrmlScene.AddNode(outVolume)
        fiducialNode = slicer.vtkMRMLAnnotationFiducialNode()
        fiducialNode.SetFiducialWorldCoordinates(seedPointCoords)
        fiducialNode.SetName('Seed Point')
        fiducialNode.Initialize(slicer.mrmlScene)
        fiducialsList = getNode('Fiducials List')
        params = {'inputVolume': inputVolume.GetID(), 'outputVolume': outVolume.GetID(), 'seed' : fiducialsList.GetID(), 'iterations' : 6} 
        self.reportProcessStatus("Starting Segmentation")
        cliNode = slicer.cli.run(slicer.modules.simpleregiongrowingsegmentation,None, params , wait_for_completion=True)
        #from time import sleep
        #sleep(3)
        self.reportProcessStatus("Finished Segmentation")

        # make a model, only param is name of output file
        modelmaker = slicer.modules.modelmaker
        mhn = slicer.vtkMRMLModelHierarchyNode()
        slicer.mrmlScene.AddNode(mhn)
        parameters = {'InputVolume': outVolume.GetID(), 'ModelSceneFile': mhn.GetID()}
        self.reportProcessStatus("Starting Modelmaker")
        cliModelNode = slicer.cli.run(modelmaker, None, parameters, wait_for_completion=True)
        self.reportProcessStatus("Finished Modelmaker")

        # output the model
        # TODO change to method without memory leaks
        outputModelNode = mhn.GetNthChildNode(0).GetAssociatedNode()
        modelStorage = outputModelNode.CreateDefaultStorageNode()
        slicer.mrmlScene.AddNode(modelStorage)
        modelStorage.SetFileName(outPath)
        modelStorage.WriteData(outputModelNode)
        self.outFile = outFile
        #sleep(3)
        self.reportProcessStatus("Wrote Model Output")

#TODO metadata
# Visualize DiffuseColor 1.0,0.0,0.0
#Visualize Orientation 180.0,180.0,0



    def uploadOutputImpl(self):
        #print "segmodeluploadoutputimpl"
        self.uploadItem(self.outFile, self.outputFolderId)


    @staticmethod
    def entryPoint():
        # parse cmd line args
        import sys
        print "seg_pipeline entrypoint"
        print sys.argv
        (script, jobId, tmpDirRoot, requestParams) = sys.argv
        print requestParams
        params = requestParams.split('?')
        print params
        params = [param.split('=') for param in params]
        requestMap = {}
        for (k,v) in params:
            requestMap[k] = v 
        pydasParams = (requestMap['email'], requestMap['apikey'], requestMap['url'])
        sp = SlicerSegPipeline(jobId, pydasParams, tmpDirRoot, requestMap['inputitemid'], requestMap['coords'], requestMap['outputitemname'], requestMap['outputfolderid'])
        sp.execute()


SlicerSegPipeline.entryPoint()


