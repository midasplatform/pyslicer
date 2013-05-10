from __main__ import vtk, slicer
import os
import json
from slicerjob import SlicerJob
import slicer_utils

class SlicerReg(SlicerJob):
    """This class implements a job executed in Slicer's Python environment - simple region growing registration"""
    loaded_input_volumes = "Loaded Input Volumes"
    finished_registration = "Finished Registration"
    wrote_transformed_volume = "Wrote Transformed Volume"
    wrote_transform = "Wrote Transform"
    
    def __init__(self, jobId, pipelineName, pydasParams, tmpDirRoot, dataDir, outDir, proxyurl, 
                 fixedVolumeFile, movingVolumeFile, fixedItemId, movingItemId, 
                 fixedFiducialsList, movingFiducialsList, transformType,
                 outputFolderId, outputVolumeName, outputTransformName):
        SlicerJob.__init__(self, jobId, pipelineName, pydasParams, tmpDirRoot, dataDir, outDir, proxyurl)
        self.fixedVolumeFile = fixedVolumeFile
        self.movingVolumeFile = movingVolumeFile
        self.fixedItemId = fixedItemId
        self.movingItemId = movingItemId
        self.fixedFiducialsList = fixedFiducialsList
        self.movingFiducialsList = movingFiducialsList
        self.transformType = transformType
        self.outputFolderId = outputFolderId
        self.outputVolumeName = outputVolumeName
        self.outputTransformName = outputTransformName

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
    
    def process(self):
        print "regmodelprocessimpl"
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
        self.report_status(self.event_process, self.loaded_input_volumes)
        outputTransform = slicer_utils.create_linear_transform()

        slicer_utils.run_fiducial_registration(fixedFiducialsList, movingFiducialsList, outputTransform, self.transformType)
        self.report_status(self.event_process, self.finished_registration)

        self.transformed_volume = self.outputVolumeName + '.mha'
        outPath = os.path.join(self.outDir, self.transformed_volume)
        # apply transform to moving image, then save volume
        movingVolume.ApplyTransformMatrix(outputTransform.GetMatrixTransformToParent())
        slicer_utils.write_storable_node(movingVolume, outPath)
        self.report_status(self.event_process, self.wrote_transformed_volume)

        self.transform = self.outputTransformName + '.tfm'
        outPath = os.path.join(self.outDir, self.transform)
        slicer_utils.write_storable_node(outputTransform, outPath)

        self.report_status(self.event_process, self.wrote_transform)

    def jobEndingNotification(self, args=None):
        if args is not None:
            reqArgs = args.copy()
        else:
            reqArgs = {}
        reqArgs['output_folder_id'] = self.outputFolderId
        reqArgs['output_volume_name'] = self.outputVolumeName
        reqArgs['output_transform_name'] = self.outputTransformName
        SlicerJob.jobEndingNotification(self, reqArgs)

if __name__ == '__main__':
    print 'reg pipeline', sys.argv
    (script, jobId, tmpDirRoot, jsonArgs) = sys.argv
    argMap = json.loads(jsonArgs)
    #print argMap
    pydasParams = (argMap['email'][0], argMap['apikey'][0], argMap['url'][0])
    (fixedItemId, movingItemId, fixedFiducialsList, movingFiducialsList,
      transformType, outputFolderId, outputVolumeName, outputTransformName) = \
      (argMap['fixed_volume_file'][0], argMap['moving_volume_file'][0],
       argMap['fixed_item_id'][0], argMap['moving_item_id'][0], 
      json.loads(argMap['fixed_fiducials'][0]), json.loads(argMap['moving_fiducials'][0]),
      argMap['transform_type'][0],  argMap['output_folder_id'][0],
      argMap['output_volume_name'][0], argMap['output_transform_name'][0]) 

    print fixed_item_id, moving_item_id
    rp = SlicerReg(self, jobId, pipelineName, pydasParams, tmpDirRoot, dataDir,
                   outDir, proxyurl, fixedVolumeFile, movingVolumeFile, 
                   fixedItemId, movingItemId, fixedFiducialsList,
                   movingFiducialsList, transformType, outputFolderId,
                   outputVolumeName, outputTransformName)
    rp.execute()


