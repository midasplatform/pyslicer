from __main__ import vtk, slicer

def create_fiducials_list(seedList):
    saml = slicer.modules.annotations.logic()
    saml.SetActiveHierarchyNodeID(saml.GetTopLevelHierarchyNodeID())
    saml.AddHierarchy()
    currentList = saml.GetActiveHierarchyNode()
    for seed in seedList:
        seedFN = slicer.vtkMRMLAnnotationFiducialNode()
        seedFN.SetFiducialWorldCoordinates(seed)
        seedFN.Initialize(slicer.mrmlScene)
        seedHN = slicer.vtkMRMLAnnotationHierarchyNode()
        seedHN.SetParentNodeID(currentList.GetID())
        seedHN.SetAssociatedNodeID(seedFN.GetID())
    return currentList

def load_volume(pathToVolume):
    (status, volume) = slicer.util.loadVolume(pathToVolume, returnNode=True)
    return volume

def create_linear_transform():
    transform = slicer.vtkMRMLLinearTransformNode()
    slicer.mrmlScene.AddNode(transform)
    return transform

def run_fiducial_registration(fixedFiducials, movingFiducials, outputTransform, transformType):
    params = {'fixedLandmarks': fixedFiducials.GetID(), 'movingLandmarks': movingFiducials.GetID(), 'saveTransform' : outputTransform.GetID(), 'transformType' : transformType} 
    cliNode = slicer.cli.run(slicer.modules.fiducialregistration, None, params, wait_for_completion=True)
    

def write_storable_node(storableNode, outfilePath):
    storageNode = storableNode.CreateDefaultStorageNode()
    slicer.mrmlScene.AddNode(storageNode)
    storageNode.SetFileName(outfilePath)
    storageNode.WriteData(storableNode)