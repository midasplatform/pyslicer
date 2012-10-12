from __main__ import vtk, slicer
from slicerprocess import SlicerPipeline
import pydas



class SlicerSegPipeline(SlicerPipeline):
    loaded_input_volume = "Loaded Input Volume"
    started_segmentation = "Starting Segmentation"
    finished_segmentation = "Finished Segmentation"
    started_modelmaker = "Starting Modelmaker"
    finished_modelmaker = "Finished Modelmaker"
    wrote_model_output = "Wrote Model Output"

    def __init__(self, jobId, pydasParams, tmpDirRoot, itemId, seed, outputItemName, outputFolderId ):
        SlicerPipeline.__init__(self, 'segmentationmodel', jobId, pydasParams, tmpDirRoot)
        self.itemId = itemId
        self.seed = seed
        self.outputItemName = outputItemName
        self.outputFolderId = outputFolderId

    def downloadInputImpl(self):
        print "segmodeldownloadinputimpl"
        self.headerFile = self.downloadItem(self.itemId)

    def define_process_events(self):
        process_events = [self.loaded_input_volume, self.started_segmentation, self.finished_segmentation, self.started_modelmaker, self.finished_modelmaker, self.wrote_model_output]
        process_events = [self.create_process_event(event_type) for event_type in process_events]
        print process_events
        return process_events
   
    def processImpl(self):
        print "segmodelprocessimpl"
        # take first two coords and multiply by -1
        # TODO something much more systematic dealing with coords
        (x, y, z) = [float(coord) for coord in self.seed.split(',')]
        seedPointCoords = (-1 * x, -1 * y, z)
  
        # create the path to the desired output file 
        outFile = self.outputItemName + '.vtp'
        outPath = os.path.join(self.outdir, outFile)

        (status, inputVolume) = slicer.util.loadVolume(self.headerFile, returnNode=True)
        self.reportProcessStatus(self.loaded_input_volume)

        outVolume = slicer.vtkMRMLScalarVolumeNode()
        slicer.mrmlScene.AddNode(outVolume)
        fiducialNode = slicer.vtkMRMLAnnotationFiducialNode()
        fiducialNode.SetFiducialWorldCoordinates(seedPointCoords)
        fiducialNode.SetName('Seed Point')
        fiducialNode.Initialize(slicer.mrmlScene)
        fiducialsList = getNode('Fiducials List')
        params = {'inputVolume': inputVolume.GetID(), 'outputVolume': outVolume.GetID(), 'seed' : fiducialsList.GetID(), 'iterations' : 6} 
        self.reportProcessStatus(self.started_segmentation)
        cliNode = slicer.cli.run(slicer.modules.simpleregiongrowingsegmentation,None, params , wait_for_completion=True)
        #from time import sleep
        #sleep(3)
        self.reportProcessStatus(self.finished_segmentation)

        # make a model, only param is name of output file
        modelmaker = slicer.modules.modelmaker
        mhn = slicer.vtkMRMLModelHierarchyNode()
        slicer.mrmlScene.AddNode(mhn)
        parameters = {'InputVolume': outVolume.GetID(), 'ModelSceneFile': mhn.GetID()}
        self.reportProcessStatus(self.started_modelmaker)
        cliModelNode = slicer.cli.run(modelmaker, None, parameters, wait_for_completion=True)
        self.reportProcessStatus(self.finished_modelmaker)

        # output the model
        # TODO change to method without memory leaks
        outputModelNode = mhn.GetNthChildNode(0).GetAssociatedNode()
        modelStorage = outputModelNode.CreateDefaultStorageNode()
        slicer.mrmlScene.AddNode(modelStorage)
        modelStorage.SetFileName(outPath)
        modelStorage.WriteData(outputModelNode)
        self.outFile = outFile
        #sleep(3)
        self.reportProcessStatus(self.wrote_model_output)

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
        parameters['token'] = pydas.session.token
        parameters['itemid'] = item_id
        parameters['count'] = 2
        parameters['element_1'] = 'Visualize'
        parameters['element_2'] = 'Visualize'
        parameters['qualifier_1'] = 'DiffuseColor'
        parameters['qualifier_2'] = 'Orientation'
        parameters['value_1'] = '[1.0,0.0,0.0]'
        parameters['value_2'] = '[180.0,180.0,0.0]'
        print parameters
        pydas.session.communicator.request(method, parameters) 





if __name__ == '__main__':
    (script, jobId, tmpDirRoot, json_args) = sys.argv
    import json
    arg_map = json.loads(json_args)
    pydasParams = (arg_map['email'][0], arg_map['apikey'][0], arg_map['url'][0])
    (input_item_id, coords, output_item_name, output_folder_id) = (arg_map['inputitemid'][0], arg_map['coords'][0], arg_map['outputitemname'][0], arg_map['outputfolderid'][0], ) 
    sp = SlicerSegPipeline(jobId, pydasParams, tmpDirRoot, input_item_id, coords, output_item_name, output_folder_id)
    sp.execute()
