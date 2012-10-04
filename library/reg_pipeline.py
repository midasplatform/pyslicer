# TODO this is a terrible HACK to add site packages to the Slicer Python
# but better than what was before, hopefully to be improved further
tmp_paths = ['/usr/lib/python2.6/dist-packages/',
             '/usr/local/lib/python2.6/dist-packages/']
import sys
sys.path.extend(tmp_paths)

from __main__ import vtk, slicer
from slicerprocess import SlicerPipeline
import pydas

import slicer_utils



class SlicerRegPipeline(SlicerPipeline):

    def __init__(self, jobId, pydasParams, tmpDirRoot, fixedItemId, movingItemId, fixedFiducialsList, movingFiducialsList, transformType, outputFolderId, outputItemName):
        SlicerPipeline.__init__(self, 'fiducialregistration', jobId, pydasParams, tmpDirRoot)
        self.fixedItemId = fixedItemId
        self.movingItemId = movingItemId
        print self.fixedItemId, self.movingItemId
        self.fixedFiducialsList = fixedFiducialsList
        self.movingFiducialsList = movingFiducialsList
        self.transformType = transformType
        self.outputFolderId = outputFolderId
        self.outputItemName = outputItemName

    def downloadInputImpl(self):
        print "segmodeldownloadinputimpl"
        print self.fixedItemId, self.movingItemId
        self.fixedVolumeFile = self.downloadItem(self.fixedItemId)
        self.movingVolumeFile = self.downloadItem(self.movingItemId)
        print self.fixedVolumeFile, self.movingVolumeFile


    def parseSeedpointsList(self, seedpointsList):    
        print 'parseSeedpointsList'
        #print seedpointsList
        #print type(seedpointsList)
        # TODO this is pretty bad
        if type(seedpointsList) == type([]) and type(seedpointsList[0]) == type([]):
            #print type(seedpointsList[0][0]) 
            if type(seedpointsList[0][0]) != type(0):
                #print "noe"
                seedpointsList = [[float(p) for p in seed] for seed in seedpointsList]
                #print seedpointsList                
        #types = [type(seed) for seed in seedpointsList]
        #print types 
        # TODO something better, email from jc
        seedpoints = [(-1 * x, -1 * y, z) for (x, y, z) in seedpointsList]
        return seedpoints

   
    def processImpl(self):
        print "segmodelprocessimpl"
        # take first two coords and multiply by -1
        # TODO something much more systematic dealing with coords

        # parse the seedpoints and create fiducials lists
        fixedFiducialsList = slicer_utils.create_fiducials_list(self.parseSeedpointsList(self.fixedFiducialsList))
        movingFiducialsList = slicer_utils.create_fiducials_list(self.parseSeedpointsList(self.movingFiducialsList))
        
        # load the volumes
        print self.fixedVolumeFile
        print self.movingVolumeFile

        fixedVolume = slicer_utils.load_volume(self.fixedVolumeFile)
        movingVolume = slicer_utils.load_volume(self.movingVolumeFile)
        self.reportProcessStatus("Loaded Input Volumes")

        outputTransform = slicer_utils.create_linear_transform()

        slicer_utils.run_fiducial_registration(fixedFiducialsList, movingFiducialsList, outputTransform, self.transformType)
        self.reportProcessStatus("Finished Registration")

        self.transformed_volume = self.outputItemName + '.mha'
        outPath = os.path.join(self.outdir, self.transformed_volume)
        # apply transform to moving image, then save volume
        movingVolume.ApplyTransformMatrix(outputTransform.GetMatrixTransformToParent())
        slicer_utils.write_storable_node(movingVolume, outPath)
        self.reportProcessStatus("Wrote Transformed Volume")

        self.transform = self.outputItemName + '.tfm'
        outPath = os.path.join(self.outdir, self.transform)
        slicer_utils.write_storable_node(outputTransform, outPath)

        self.reportProcessStatus("Wrote Transform")

    def uploadOutputImpl(self):
        #print "segmodeluploadoutputimpl"
        (email, apiKey, url) = self.pydasParams
        pydas.login(email=email, api_key=apiKey, url=url)
        folder = pydas.communicator.create_folder(pydas.token, 'output_'+self.jobId, self.outputFolderId)
        folder_id = folder['folder_id'] 
        item_id = self.uploadItem(self.transformed_volume, folder_id, self.transformed_volume)
        item_id = self.uploadItem(self.transform, folder_id, self.transform)
 


if __name__ == '__main__':
    print 'reg pipeline', sys.argv
    (script, jobId, tmpDirRoot, json_args) = sys.argv
    import json
    arg_map = json.loads(json_args)
    #print arg_map
    pydasParams = (arg_map['email'][0], arg_map['apikey'][0], arg_map['url'][0])
    (fixed_item_id, moving_item_id, fixed_fiducials, moving_fiducials, transform_type, output_folder_id, output_item_name) = (arg_map['fixed_item_id'][0], arg_map['moving_item_id'][0], json.loads(arg_map['fixed_fiducials'][0]), json.loads(arg_map['moving_fiducials'][0]),  arg_map['transform_type'][0],  arg_map['output_folder_id'][0],  arg_map['output_item_name'][0], ) 
    print fixed_item_id, moving_item_id
    rp = SlicerRegPipeline(jobId, pydasParams, tmpDirRoot, fixed_item_id, moving_item_id, fixed_fiducials, moving_fiducials, transform_type, output_folder_id, output_item_name)
    rp.execute()


#    http://localhost:8880/slicerjob/init/?pipeline=registration&url=http://localhost/midas3&email=michael.grauer@kitware.com&apikey=dcc90e81da77d774bcaf44c4c1d9648c&fixed_item_id=1778&moving_item_id=1930&fixed_fiducials=[[-81,-107,90],[-129,-133.4,90],[-127.5,-155,90],[-179,-101,90],[-83.5,-164,90]]&moving_fiducials=[[-101,-107,90],[-149,-133.4,90],[-147.5,-155,90],[-199,-101,90],[-103.5,-164,90]]&transform_type=Rigid&output_folder_id=896&output_item_name=s1_transformed&job_id=90