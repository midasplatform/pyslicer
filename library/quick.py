from __main__ import vtk, slicer
import vtk.util.numpy_support
import os
import sys
import pydas
import zipfile
import shutil



def createTmpDir():
    tmpdirpath = 'tmpdir'
    # clear it out if it already exists
    if(os.path.exists(tmpdirpath)):
        removeTmpDir(tmpdirpath)
    os.mkdir(tmpdirpath)  
    return tmpdirpath
 
def removeTmpDir(tmpdir):
    shutil.rmtree(tmpdir)


def pydasConnection(url, email, api_key):
    pydas.login(email=email, api_key=api_key, url=url)



def downloadItem(tmpdir, item_id):
    # create a data dir
    datadir = os.path.join(tmpdir, 'data')
    os.mkdir(datadir)  
    pydas._download_item(item_id, datadir)
    # unzip any zipped files
    for filename in os.listdir(datadir):
        if filename.endswith('.zip'):
            filepath = os.path.join(datadir, filename)
            zip = zipfile.ZipFile(filepath)
            zip.extractall(datadir)
            zip.close()
    # look for the header file or mha, this is very brittle
    for filename in os.listdir(datadir):
        if filename.endswith('.nhdr') or filename.endswith('.mha'):
            return os.path.join(datadir, filename)
   

# TODO this is just a stub for whatever processing we want to occur 
def changeIntensity(tmpdir, headerfile):
    outdir = os.path.join(tmpdir, 'out')
    os.mkdir(outdir)
    mrml = slicer.vtkMRMLScene()
    storageNode = slicer.vtkMRMLVolumeArchetypeStorageNode()
    # specifiying as mha
    outPath = os.path.join(outdir, 'output.mha')
    storageNode.SetFileName(outPath)
    
    vl = slicer.vtkSlicerVolumesLogic()
    vl.SetAndObserveMRMLScene(mrml)
    n = vl.AddArchetypeVolume(headerfile, 'CTC')
    i = n.GetImageData()
    a = vtk.util.numpy_support.vtk_to_numpy(i.GetPointData().GetScalars())
    
    # change the intensity
    a[:] = a.max()/2 - a 
    
    storageNode.WriteData(n)
    return outdir

   
# TODO very hackish in terms of copying everything up as a single item
# may want to actually read headers and create items based on correspondence or something else
# to manage header and content 
def uploadOutput(outdir, parent_folder_id, output_item_name):
    # read everything in the outdir and upload it as a single item
    # create a new item
    # need a folder id
    item = pydas.communicator.create_item(pydas.token, output_item_name, parent_folder_id) 
    item_id = item['item_id']
    print "output_item_id="+item_id
    for filename in os.listdir(outdir):
        upload_token = pydas.communicator.generate_upload_token(pydas.token, item_id, filename)
        filepath=os.path.join(outdir, filename)
        pydas.communicator.perform_upload(upload_token, filename, itemid=item_id, filepath=filepath)
    





def runDemo():
    (script, url, email, api_key, item_id, parent_folder_id, output_item_name) = sys.argv
    pydasConnection(url, email, api_key)
    tmpdir = createTmpDir()
    headerfile = downloadItem(tmpdir, item_id)
    outdir = changeIntensity(tmpdir, headerfile)
    uploadOutput(outdir, parent_folder_id, output_item_name)
    removeTmpDir(tmpdir)
    slicer.app.exit()

runDemo()
