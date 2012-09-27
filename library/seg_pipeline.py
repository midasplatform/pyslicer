# TODO this is a terrible HACK to add site packages to the Slicer Python
# but better than what was before, hopefully to be improved further
tmp_paths = ['/usr/lib/python2.6/dist-packages/',
             '/usr/local/lib/python2.6/dist-packages/',
             '/usr/lib/python2.7/dist-packages/',
             '/usr/local/lib/python2.7/dist-packages/']
import sys
sys.path.extend(tmp_paths)

from __main__ import vtk, slicer
from slicerprocess import SlicerPipeline
import pydas



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
        item_id = self.uploadItem(self.outFile, self.outputFolderId)
        (email, apiKey, url) = self.pydasParams
        pydas.login(email=email, api_key=apiKey, url=url)
        # TODO move metadata to superclass
        # set metadata on the output item
        method = 'midas.item.setmultiplemetadata'
        parameters = {}
        parameters['token'] = pydas.token
        parameters['itemid'] = item_id
        parameters['count'] = 2
        parameters['element_1'] = 'Visualize'
        parameters['element_2'] = 'Visualize'
        parameters['qualifier_1'] = 'DiffuseColor'
        parameters['qualifier_2'] = 'Orientation'
        parameters['value_1'] = '[1.0,0.0,0.0]'
        parameters['value_2'] = '[180.0,180.0,0.0]'
        print parameters
        pydas.communicator.request(method, parameters) 

    def process(self):
        self.reportStatus(self.event_process)
        self.processImpl()        





if __name__ == '__main__':
    (script, jobId, tmpDirRoot, requestParams) = sys.argv
    params = requestParams.split('?')
    params = [param.split('=') for param in params]
    requestMap = {}
    for (k,v) in params:
        requestMap[k] = v 
    pydasParams = (requestMap['email'], requestMap['apikey'], requestMap['url'])
    sp = SlicerSegPipeline(jobId, pydasParams, tmpDirRoot, requestMap['inputitemid'], requestMap['coords'], requestMap['outputitemname'], requestMap['outputfolderid'])
    sp.execute()
    


#    @staticmethod
#    def entryPoint():
#        # parse cmd line args
#        import sys
#        print "seg_pipeline entrypoint"
#        print sys.argv
#        (script, jobId, tmpDirRoot, requestParams) = sys.argv
#        print requestParams
#        params = requestParams.split('?')
#        print params
#        params = [param.split('=') for param in params]
#        requestMap = {}
#        for (k,v) in params:
#            requestMap[k] = v 
#        pydasParams = (requestMap['email'], requestMap['apikey'], requestMap['url'])
#        sp = SlicerSegPipeline(jobId, pydasParams, tmpDirRoot, requestMap['inputitemid'], requestMap['coords'], requestMap['outputitemname'], requestMap['outputfolderid'])
#        sp.execute()
#    
