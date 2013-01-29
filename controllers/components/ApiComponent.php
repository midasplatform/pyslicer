<?php
/*=========================================================================
 MIDAS Server
 Copyright (c) Kitware SAS. 26 rue Louis Guérin. 69100 Villeurbanne, FRANCE
 All rights reserved.
 More information http://www.kitware.com

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

         http://www.apache.org/licenses/LICENSE-2.0.txt

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
=========================================================================*/


/** Component for api methods */
class Pyslicer_ApiComponent extends AppComponent
{


  /**
   * Helper function for verifying keys in an input array
   */
  private function _checkKeys($keys, $values)
    {
    foreach($keys as $key)
      {
      if(!array_key_exists($key, $values))
        {
        throw new Exception('Parameter '.$key.' must be set.', -1);
        }
      }
    }
    
  /** Return the user dao */
  private function _getUser($args)
    {
    $authComponent = MidasLoader::loadComponent('Authentication', 'api');
    return $authComponent->getUser($args, Zend_Registry::get('userSession')->Dao);
    }

  /**
   * start processing on an item
   * @param item_id The id of the item to be processed
   * @param output_item_name The name of the created output item
   * @param seed The x,y,z point coords of the seed point
   * @param output_folder_id (optional) The id of the folder where the output item
     will be created, if not supplied, the first parent folder found on the input
     item will be used as the output folder.
     @param job_name (optional) The name of the processing job, if not supplied,
     will be given a name like "Slicer Job X" where x is the job id.
   * @return redirect => redirectURL.
   */
  public function startItemProcessing($args)
    {
    // TODO probably want some notion of which script to run
    // maybe get that as an item? or from the terminal? or from a list?
      
    $this->_checkKeys(array('item_id', 'output_item_name', 'seed'), $args);    
    $userDao = $this->_getUser($args);
    if(!$userDao)
      {
      throw new Exception('Anonymous users may not process items', MIDAS_PYSLICER_INVALID_POLICY);
      }

    $itemModel = MidasLoader::loadModel('Item');
    $folderModel = MidasLoader::loadModel('Folder');
    
    $itemId = $args['item_id'];
    $outputItemName = $args['output_item_name'];
    // TODO pass along the seed
    $seed = JsonComponent::decode($args['seed']);
    
    // check the input item
    $itemDao = $itemModel->load($itemId);
    if($itemDao === false)
      {
      throw new Zend_Exception('This item does not exist.', MIDAS_PYSLICER_INVALID_PARAMETER);
      }
    if(!$itemModel->policyCheck($itemDao, $userDao, MIDAS_POLICY_READ))
      {
      throw new Zend_Exception('Read access on this item required.', MIDAS_PYSLICER_INVALID_POLICY);
      }
    
    // check the output folder
    if(isset($args['output_folder_id']))
      {
      $outputFolderId = $args['output_folder_id'];  
      $parentFolder = $folderModel->load($outputFolderId);
      }
    else
      {
      $parentFolders = $itemDao->getFolders();
      $parentFolder = $parentFolders[0];
      }
    if($parentFolder === false)
      {
      throw new Zend_Exception('This output folder does not exist.', MIDAS_PYSLICER_INVALID_PARAMETER);
      }
    if(!$folderModel->policyCheck($parentFolder, $userDao, MIDAS_POLICY_WRITE))
      {
      throw new Zend_Exception('Write access on this folder required.', MIDAS_PYSLICER_INVALID_POLICY);
      }
      
    $userEmail = $userDao->getEmail();
    // get an api key for this user
    $userApiModel = MidasLoader::loadModel('Userapi', 'api');
    $userApiDao = $userApiModel->getByAppAndUser('Default', $userDao);
    if(!$userApiDao)
      {
      throw new Zend_Exception('You need to create a web-api key for this user for application: Default');
      }

    // TODO store remote processing job info
    $jobModel = MidasLoader::loadModel('Job', 'remoteprocessing');
    $job = MidasLoader::newDao('JobDao', 'remoteprocessing');
    $job->setCreatorId($userDao->getUserId());
    $job->setStatus(MIDAS_REMOTEPROCESSING_STATUS_WAIT);
    // TODO hard coded script and params
    $segmentationPipeline = 'segmentation';
    $job->setScript($segmentationPipeline);
    // TODO json encode params set
    $job->setParams(JsonComponent::encode($seed));
    $jobModel->save($job);    
    $jobModel->addItemRelation($job, $itemDao, MIDAS_REMOTEPROCESSING_RELATION_TYPE_INPUT);

    if(isset($args['job_name']))
      {
      $jobName = $args['job_name'];  
      }
    else
      {
      $jobName = 'Slicer Job ' . $job->getKey();
      }
    $job->setName($jobName);
    $jobModel->save($job);    
    
    // TODO store twisted server url in config
    $settingModel = MidasLoader::loadModel('Setting');
    $twistedServerUrl = $settingModel->getValueByName('slicerProxyUrl', 'pyslicer');
    
    // TODO switch to different pipeline types
    $jobInitPath = "/slicerjob/init/";
    
    $midasPath = Zend_Registry::get('webroot');
    $midasUrl = 'http://' . $_SERVER['HTTP_HOST'] . $midasPath;
    $apiKey = $userApiDao->getApikey();
    $parentFolderId = $parentFolder->getFolderId();

    // TODO probably a security hole to put the email and api key in the url
    // TODO hardcoded seed
    //$seed = "-93.5,-82.2,89.9";
    $slicerjobParams = array('pipeline' => $segmentationPipeline,
                             'url' => $midasUrl,
                             'email' => $userEmail,
                             'apikey' => $apiKey,
                             'inputitemid' => $itemId,
        // TODO some formatting/error checking on seeds
                             'coords' => $seed[0] . ',' . $seed[1] . ',' . $seed[2],
                             'outputfolderid' => $parentFolderId,
                             'outputitemname' => $outputItemName,
                             'job_id' => $job->getKey());
    $requestParams = "";
    $ind = 0;
    foreach ($slicerjobParams as $name => $value)
      {
      if ($ind > 0)
        {
        $requestParams .= "&";
        }
      $requestParams .= $name . '=' . $value;
      $ind++;
      }
    
    $url = $twistedServerUrl . $jobInitPath . '?' . $requestParams;
    // TODO what if the url isn't there?  no server?  what do we get back?
    // we get back false, and should take some appropriate action for the
    // return value here
    
    $data = file_get_contents($url);  
   
    
    // TODO clean up this redirect code, we are no longer expecting an item id
    
    // if we get back an output item id in the synchronous case, redirect to that
    // regardless of what we get back, should return a redirect URL
    //$outputItemKey = 'output_item_id=';
    if($data === false)
      {
      throw new Zend_Exception("Cannot connect with Slicer Server.");  
      }
    /*elseif(strpos($data, $outputItemKey) === 0)
      {
      $outputItemId = substr($data, strlen($outputItemKey));
      $redirectURL = $midasPath . '/visualize/paraview/slice?itemId='.$itemId.'&meshes='.$outputItemId.'&jsImports=/midas/modules/pyslicer/public/js/lib/visualize.meshView.js';
      return array('redirect' => $redirectURL);
      }*/
    else
      {
      $redirectURL = $midasUrl . '/pyslicer/process/status?jobId='.$job->getJobId();
      return array('redirect' => $redirectURL);
      //throw new Zend_Exception("No output_item_id supplied, server says: ". $data);
      }
    }

    
  protected function _loadValidItem($userDao, $itemId, $paramName)
    {
    $itemModel = MidasLoader::loadModel('Item');
    $itemDao = $itemModel->load($itemId);
    if($itemDao === false)
      {
      throw new Zend_Exception('The item for '.$paramName.' does not exist.', MIDAS_PYSLICER_INVALID_PARAMETER);
      }
    if(!$itemModel->policyCheck($itemDao, $userDao, MIDAS_POLICY_READ))
      {
      throw new Zend_Exception('Read access on the item for '.$paramName.' is required.', MIDAS_PYSLICER_INVALID_POLICY);
      }
    return $itemDao;
    }
   
  protected function _findValidOutputFolderId($userDao, $outputFolderId=false)
    {
    $folderModel = MidasLoader::loadModel('Folder');

    // validate output folder for user writing
    if($outputFolderId)
      {
      $outputFolder = $folderModel->load($outputFolderId);
      if($outputFolder === false || !$folderModel->policyCheck($outputFolder, $userDao, MIDAS_POLICY_WRITE))
        {
        $outputFolderId = false;
        }  
      }
    
    if(!$outputFolderId)
      {
      $outputFolderId = $userDao->getFolderId();  
      }
      
    return $outputFolderId;  
    }
      
  protected function _getConnectionParams($userDao)
    {
    $userEmail = $userDao->getEmail();
    
    $midasPath = Zend_Registry::get('webroot');
    $midasUrl = 'http://' . $_SERVER['HTTP_HOST'] . $midasPath;
    
    $userApiModel = MidasLoader::loadModel('Userapi', 'api');
    $userApiDao = $userApiModel->getByAppAndUser('Default', $userDao);
    if(!$userApiDao)
      {
      throw new Zend_Exception('You need to create a web-api key for this user for application: Default');
      }
    $apiKey = $userApiDao->getApikey();      
    
    return array($userEmail, $apiKey, $midasUrl);
    }

    
  // output_item_name will be set in job creation if it does not exist
  // job_name will be set in job creation if it does not exist
  // params will be modified if needed to set output_item_name
  protected function _createJob($userDao, $script, $params, $inputItems, $synthesizedItemNames, $jobName=false)
    { 
    $jobModel = MidasLoader::loadModel('Job', 'remoteprocessing');
    $job = MidasLoader::newDao('JobDao', 'remoteprocessing');
    $job->setCreatorId($userDao->getUserId());
    $job->setStatus(MIDAS_REMOTEPROCESSING_STATUS_WAIT);
    $job->setScript($script);
    $jobModel->save($job);
    foreach($inputItems as $itemDao)
      {
      $jobModel->addItemRelation($job, $itemDao, MIDAS_REMOTEPROCESSING_RELATION_TYPE_INPUT);
      }

    // now that a job id is defined...
    if(!$jobName)
      {
      $jobName = 'Slicer Job ' . $job->getJobId();
      }
    $job->setName($jobName);
    
    // synthesize names for any params if needed
    foreach($synthesizedItemNames as $id => $nameSuffix)
      {
      if(!$params[$id])
        {
        $jobName = $job->getName();
        $jobName = str_replace(" ", "_", $jobName);
        $outputItemName = $jobName . $nameSuffix;
        $params[$id] = $outputItemName;
        }
      }
    
    $job->setParams(JsonComponent::encode($params));
    $jobModel->save($job);    
    return array($job, $params);
    }

  protected function _constructJobCreationUrl($userDao, $script, $job, $params)
    {
    // TODO store twisted server url in config
    $settingModel = MidasLoader::loadModel('Setting');
    $twistedServerUrl = $settingModel->getValueByName('slicerProxyUrl', 'pyslicer');
    $jobInitPath = "/slicerjob/init/";
    // TODO probably a security hole to put the email and api key in the url
    // TODO hardcoded seed
    list($userEmail, $apiKey, $midasUrl) = $this->_getConnectionParams($userDao);    
    $jobParams = array('pipeline' => $script,
                       'url' => $midasUrl,
                       'email' => $userEmail,
                       'apikey' => $apiKey,
                       'job_id' => $job->getJobId());
    $jobParams = array_merge($jobParams, $params);
    $requestParams = "";
    $ind = 0;
    foreach ($jobParams as $name => $value)
      {
      if ($ind > 0)
        {
        $requestParams .= "&";
        }
      $requestParams .= $name . '=' . $value;
      $ind++;
      }
    
    $url = $twistedServerUrl . $jobInitPath . '?' . $requestParams;
    return array($url, $midasUrl);
    }
   
    
    
    
    
    
    
    
    
  /**
   * start a fiducial registration job
   * @param fixed_item_id The id of the fixed image item to be processed
   * @param moving_item_id The id of the image image item to be processed
   * @param fixed_fiducials json encoded list of 3D points
   * @param moving_fiducials json encoded list of 3D points
   * @param transform_type one of [Rigid|Translation|Similarity]
   * @param output_folder_id (optional) The id of the folder to create an output
     folder underneath.  If not supplied the user's Private folder will be used.
   * @param output_volume_name (optional) The name of the created output volume 
     item.  If not supplied a name like "Slicer_Job_X_output_volume will be created.
   * @param output_transform_name (optional) The name of the created output transform 
     item.  If not supplied a name like "Slicer_Job_X_output_transform will be created.
   * @param job_name (optional) The name of the processing job, if not supplied,
     will be given a name like "Slicer Job X" where x is the job id.
   * @return redirect => redirectURL.
   */
  public function startFiducialregistration($args)
    {
    $this->_checkKeys(array('fixed_item_id', 'moving_item_id', 'fixed_fiducials', 'moving_fiducials', 'fixed_fiducials', 'transform_type'), $args);    
    $userDao = $this->_getUser($args);
    if(!$userDao)
      {
      throw new Exception('Anonymous users may not process items', MIDAS_PYSLICER_INVALID_POLICY);
      }

    $fixedItem = $this->_loadValidItem($userDao, $args['fixed_item_id'], 'fixed_item_id');
    $movingItem = $this->_loadValidItem($userDao, $args['moving_item_id'], 'moving_item_id');
    $fixedFiducials = JsonComponent::decode($args['fixed_fiducials']);
    $movingFiducials = JsonComponent::decode($args['moving_fiducials']);
    $outputFolderId = $this->_findValidOutputFolderId($userDao, 
                                                      isset($args['output_folder_id']) ? $args['output_folder_id'] : false);
    $transformType = $args['transform_type'];
    $transforms = array('Rigid', 'Translation', 'Similarity');
    if(!in_array($transformType, $transforms))
      {
      throw new Zend_Exception('transform_type must be one of Rigid, Translation or Similarity.');
      }
    
    $inputItems = array($fixedItem, $movingItem);
    $script = MIDAS_PYSLICER_REGISTRATION_PIPELINE;
    $params = array('fixed_item_id' => $fixedItem->getItemId(),
                    'moving_item_id' => $movingItem->getItemId(),
                    'fixed_fiducials' => JsonComponent::encode($fixedFiducials),
                    'moving_fiducials' => JsonComponent::encode($movingFiducials),
                    'transform_type' => $transformType,
                    'output_folder_id' => $outputFolderId,
                    'output_volume_name' => isset($args['output_volume_name']) ? $args['output_volume_name'] : false,
                    'output_transform_name' => isset($args['output_transform_name']) ? $args['output_transform_name'] : false);
    $synthesizedItemNames = array('output_volume_name' => '_output_volume',
                                  'output_transform_name' => '_output_transform');
    
    // output_volume_name and output_transform_name will be set in job creation 
    // if they do not exist
    // job_name will be set in job creation if it does not exist
    list($job, $params) = $this->_createJob($userDao, $script, $params, $inputItems, $synthesizedItemNames,
                             isset($args['job_name']) ? $args['job_name'] : false);
    
    list($jobCreationUrl, $midasUrl) = $this->_constructJobCreationUrl($userDao, $script, $job, $params);
    
    $data = file_get_contents($jobCreationUrl);  
   
    if($data === false)
      {
      throw new Zend_Exception("Cannot connect with Slicer Server.");  
      }
    else
      {
      $redirectURL = $midasUrl . '/pyslicer/process/status?jobId='.$job->getJobId();
      return array('redirect' => $redirectURL);
      }
    }

      
    

  /**
   * gets the count of jobs for the user on a status category basis
   * @return array ('wait' => waitingJobsCount, 'started' => startedJobsCount, 'done' => doneJobsCount, 'error' => errorJobsCount)
   */
  public function getUserJobCountsByStatus($args)
    {
    $userDao = $this->_getUser($args);
    if(!$userDao)
      {
      $jobCounts = array('wait' => 0, 'started' => 0, 'done' => 0);
      }
    else
      {
      $jobModel = MidasLoader::loadModel('Job', 'remoteprocessing');
      $jobs = $jobModel->findBy('creator_id', $userDao->getKey());
      $jobsByStatus = array(MIDAS_REMOTEPROCESSING_STATUS_WAIT => 0,
                MIDAS_REMOTEPROCESSING_STATUS_STARTED => 0,
                MIDAS_REMOTEPROCESSING_STATUS_DONE => 0,
                MIDAS_PYSLICER_REMOTEPROCESSING_JOB_EXCEPTION => 0);
      foreach($jobs as $job)
        {
        $jobsByStatus[$job->getStatus()]++;  
        }
      $jobCounts= array('wait' => $jobsByStatus[MIDAS_REMOTEPROCESSING_STATUS_WAIT],
                        'started' => $jobsByStatus[MIDAS_REMOTEPROCESSING_STATUS_STARTED],
                        'done' => $jobsByStatus[MIDAS_REMOTEPROCESSING_STATUS_DONE],
                        'error' => $jobsByStatus[MIDAS_PYSLICER_REMOTEPROCESSING_JOB_EXCEPTION]);
      }
    return $jobCounts;
    }
    
  /**
   * update the status of a job
   * @param job_id the id of the job to update
   * @param status the current status of the job
   * @param condition (optional) a condition message for the job (currently
     only used for exceptions, status=3
   * @return array('success' => 'true') if successful.
   */
  public function updateJob($args)
    {
    $this->_checkKeys(array('job_id', 'status'), $args);    
    $userDao = $this->_getUser($args);
    if(!$userDao)
      {
      throw new Exception('Anonymous users may not update job statuses', MIDAS_PYSLICER_INVALID_POLICY);
      }
      
    $jobModel = MidasLoader::loadModel('Job', 'remoteprocessing');
    $jobId = $args['job_id'];
    $job = $jobModel->load($jobId);
    if($job === false)
      {
      throw new Zend_Exception('This job does not exist.', MIDAS_PYSLICER_INVALID_PARAMETER);
      }
    if($job->getCreatorId() != $userDao->getUserId())
      {
      throw new Exception('Only the job owner can update its status', MIDAS_PYSLICER_INVALID_POLICY);
      }

    $status = $args['status'];
    $job->setStatus($status);

    if(isset($args['condition']))
      {
      $condition = $args['condition'];  
      $job->setCondition($condition);
      }
    $jobModel->save($job);
    
    return array('success' => 'true');
    }
    
  /**
   * notify a jobstatus that it has occurred
   * @param jobstatus_id the id of the jobstatus to update
   * @param notify_date the unix timestamp for the event
   * @return array('success' => 'true') if successful.
   */
  public function notifyJobstatus($args)
    {
    $this->_checkKeys(array('jobstatus_id', 'notify_date'), $args);    
    $userDao = $this->_getUser($args);
    if(!$userDao)
      {
      throw new Exception('Anonymous users may not notify jobstatus', MIDAS_PYSLICER_INVALID_POLICY);
      }

    $jobstatusModel = MidasLoader::loadModel('Jobstatus', 'pyslicer');
    $jobstatus = $jobstatusModel->load($args['jobstatus_id']);
    if($jobstatus === false)
      {
      throw new Zend_Exception('This jobstatus does not exist.', MIDAS_PYSLICER_INVALID_PARAMETER);
      }

    $job = $jobstatus->getJob();    
    if($job->getCreatorId() != $userDao->getUserId())
      {
      throw new Exception('Only the job owner can update an associated jobstatus', MIDAS_PYSLICER_INVALID_POLICY);
      }
    
    $notifyDate = date('Y-m-d H:i:s', $args['notify_date']);
    $jobstatus->setNotifyDate($notifyDate);  
    $jobstatusModel->save($jobstatus);      
      
    return array('success' => 'true');
    }
    
    
  /**
   * add a json encoded list of eventual events, that have not yet
   * occurred, will create jobstatus for these and return an array
   * mapping event_id to jobstatus_id, all of these events should have
   * the same value for remoteprocessing_job_id, that is, they should
   * all be part of the same job.
   * @param events json encoded list of events, all with the same remoteprocessing_job_id
   * @return array (event_id => jobstatus_id) if successful.
   */
  public function addJobstatuses($args)
    {
    $this->_checkKeys(array('events'), $args);    
    $userDao = $this->_getUser($args);
    if(!$userDao)
      {
      throw new Exception('Anonymous users may not add jobstatuses', MIDAS_PYSLICER_INVALID_POLICY);
      }

    $jobModel = MidasLoader::loadModel('Job', 'remoteprocessing');
    $jobstatusModel = MidasLoader::loadModel('Jobstatus', 'pyslicer');
    
    $events = JsonComponent::decode($args['events']);
    $eventIdsToJobstatusIds = array();
    foreach($events as $event)
      {
      $jobstatus = MidasLoader::newDao('JobstatusDao', 'pyslicer');
      $eventParts = explode('&', $event);
      foreach($eventParts as $part)
        {
        $property = explode('=', $part);
        if(sizeof($property) == 2)
          {
          // ignore timestamp as we are just adding eventual events here
          $name = $property[0];
          $value = $property[1];
          if($name != 'timestamp')
            {
            $jobstatus->set($property[0], $property[1]);  
            }
          }
        }
      // before saving the jobstatus, ensure that the job is valid
      // and the user is the owner
      $job = $jobModel->load($jobstatus->getRemoteprocessingJobId());
      if($job === false)
        {
        throw new Zend_Exception('Job '.$jobstatus->getRemoteprocessingJobId().' does not exist.', MIDAS_PYSLICER_INVALID_PARAMETER);
        }
      if($job->getCreatorId() != $userDao->getUserId())
        {
        throw new Exception('Only the job owner can update its status', MIDAS_PYSLICER_INVALID_POLICY);
        }
      $jobstatusModel->save($jobstatus);      
      $eventIdsToJobstatusIds[$jobstatus->getEventId()] = $jobstatus->getJobstatusId();
      }
    return $eventIdsToJobstatusIds;
    }
    
  /**
   * will return a job object for a job_id with the current status,
   * along with any related jobstatus objects for that job.
   * @param job_id the id of the job to query status for.
   * @return array ('job' => the job object,
                    'jobstatuses' => the array of jobstatus objects,
                    'condition_rows' => array of job condition lines, if any,
                    'output_links' => array of output links for this job, if any).
   */
  public function getJobstatus($args)
    {
    $this->_checkKeys(array('job_id'), $args);    
    $userDao = $this->_getUser($args);
    if(!$userDao)
      {
      throw new Exception('Anonymous users may not get job status', MIDAS_PYSLICER_INVALID_POLICY);
      }

    $jobModel = MidasLoader::loadModel('Job', 'remoteprocessing');
    $jobstatusModel = MidasLoader::loadModel('Jobstatus', 'pyslicer');

    $job = $jobModel->load($args['job_id']);
    if($job === false)
      {
      throw new Zend_Exception('Job '.$args['job_id'].' does not exist.', MIDAS_PYSLICER_INVALID_PARAMETER);
      }
    if($job->getCreatorId() != $userDao->getUserId())
      {
      throw new Exception('Only the job owner can query its status', MIDAS_PYSLICER_INVALID_POLICY);
      }

    // get the status details
    $jobstatuses = $jobstatusModel->getForJob($job);
    
    $pipelineComponent = MidasLoader::loadComponent('Pipeline', 'pyslicer');
    $conditionRows = $pipelineComponent->formatJobCondition($job->getCondition());
    $inputsAndOutputs = $pipelineComponent->resolveInputsAndOutputs($job);
    return array('job' => $job, 'jobstatuses' => $jobstatuses, 'condition_rows' => $conditionRows, 'output_links' => $inputsAndOutputs['outputs']);  
    }
    
    

  /**
   * add an output item to a job
   * @param job_id the id of the job to update
   * @param item_id the id of the item to set as an output of the job
   * @return array('success' => 'true') if successful.
   */
  public function addJobOutputItem($args)
    {
    $this->_checkKeys(array('job_id', 'item_id'), $args);    
    $userDao = $this->_getUser($args);
    if(!$userDao)
      {
      throw new Exception('Anonymous users may not update jobs', MIDAS_PYSLICER_INVALID_POLICY);
      }
      
    $jobModel = MidasLoader::loadModel('Job', 'remoteprocessing');
    $jobId = $args['job_id'];
    $job = $jobModel->load($jobId);
    if($job === false)
      {
      throw new Zend_Exception('This job does not exist.', MIDAS_PYSLICER_INVALID_PARAMETER);
      }
    if($job->getCreatorId() != $userDao->getUserId())
      {
      throw new Exception('Only the job owner can update it', MIDAS_PYSLICER_INVALID_POLICY);
      }

    $itemId = $args['item_id'];
    $itemModel = MidasLoader::loadModel('Item');
    $item = $itemModel->load($itemId);
    if($item === false)
      {
      throw new Zend_Exception('This item does not exist.', MIDAS_PYSLICER_INVALID_PARAMETER);
      }

    $jobModel->addItemRelation($job, $item, MIDAS_REMOTEPROCESSING_RELATION_TYPE_OUPUT);

    return array('success' => 'true');
    }
    
    
    
} // end class




