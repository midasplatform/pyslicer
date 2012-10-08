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
require_once BASE_PATH . '/modules/pyslicer/AppController.php';

/** pyslicer process controller*/
class Pyslicer_ProcessController extends Pyslicer_AppController
{

  public $_models = array('Item', 'Folder');
  protected $statusStrings =
    array(MIDAS_REMOTEPROCESSING_STATUS_WAIT => 'waiting',
          MIDAS_REMOTEPROCESSING_STATUS_STARTED => 'started',
          MIDAS_REMOTEPROCESSING_STATUS_DONE => 'done',
          MIDAS_PYSLICER_REMOTEPROCESSING_JOB_EXCEPTION => 'error');
  protected $statusClasses =
    array(MIDAS_REMOTEPROCESSING_STATUS_WAIT => 'midas_pyslicer_wait',
          MIDAS_REMOTEPROCESSING_STATUS_STARTED => 'midas_pyslicer_started',
          MIDAS_REMOTEPROCESSING_STATUS_DONE => 'midas_pyslicer_done',
          MIDAS_PYSLICER_REMOTEPROCESSING_JOB_EXCEPTION => 'midas_pyslicer_error');
  
  protected $pipelines = array(
        MIDAS_PYSLICER_SEGMENTATION_PIPELINE => array(
           MIDAS_PYSLICER_EXPECTED_INPUTS => MIDAS_PYSLICER_SEGMENTATION_INPUT_COUNT,
           MIDAS_PYSLICER_EXPECTED_OUTPUTS => MIDAS_PYSLICER_SEGMENTATION_OUTPUT_COUNT,
           MIDAS_PYSLICER_INPUT_GENERATOR => 'segmentationInputLinks',
           MIDAS_PYSLICER_OUTPUT_GENERATOR => 'segmentationOutputLinks'),
        MIDAS_PYSLICER_REGISTRATION_PIPELINE => array(
           MIDAS_PYSLICER_EXPECTED_INPUTS => MIDAS_PYSLICER_REGISTRATION_INPUT_COUNT,
           MIDAS_PYSLICER_EXPECTED_OUTPUTS => MIDAS_PYSLICER_REGISTRATION_OUTPUT_COUNT,
           MIDAS_PYSLICER_INPUT_GENERATOR => 'registrationInputLinks',
           MIDAS_PYSLICER_OUTPUT_GENERATOR => 'registrationOutputLinks'));
  
  /** init method */
  function init()
    {
    }

    
  function segmentationInputLinks($job, $inputs, $outputs, $midasPath)
    {
    $inputItemId = $inputs[0]->getItemId();
    $inputLink = $midasPath . '/visualize/paraview/slice?itemId='.$inputItemId;
    $inputLinkText = 'View Input';
    return array( array ('text' => $inputLinkText, 'url' => $inputLink));
    }

  function segmentationOutputLinks($job, $inputs, $outputs, $midasPath)
    {
    $inputItemId = $inputs[0]->getItemId();
    $outputItemId = $outputs[0]->getItemId();
    $outputLink = $midasPath . '/visualize/paraview/slice?itemId='.$inputItemId.'&meshes='.$outputItemId.'&jsImports='.$midasPath.'/modules/pyslicer/public/js/lib/visualize.meshView.js';
    $outputLinkText = 'View Output';  
    return array( array ('text' => $outputLinkText, 'url' => $outputLink));
    }
  
  function registrationInputLinks($job, $inputs, $outputs, $midasPath)
    {
    $fixedItemId = $inputs[0]->getItemId();
    $movingItemId = $inputs[1]->getItemId();
    $inputLink = $midasPath . '/visualize/paraview/dual?left='.$fixedItemId;
    $inputLink .= '&right=' . $movingItemId;
    $inputLinkText = 'View Input';
    return array( array ('text' => $inputLinkText, 'url' => $inputLink));
    }

  function registrationOutputLinks($job, $inputs, $outputs, $midasPath)
    {
    $params = JsonComponent::decode($job->getParams());
    $fixedItemId = $params['fixed_item_id'];
    
    // we need to get the output volume, but there are two outputs
    // we know the fact that the output volume is created first
    // and the outputs here are returned in reverse order of creation, but
    // those seem like brittle facts to rely on.
    // it seems better to check the description
    $outputVolumeId = -1;
    foreach($outputs as $output)
      {
      if($output->getDescription() == MIDAS_PYSLICER_REGISTRATION_OUTPUT_VOLUME_DESCRIPTION)
        {
        $outputVolumeId = $output->getItemId();
        }
      }
    
    $outputLink = $midasPath . '/visualize/paraview/dual?left='.$fixedItemId;
    $outputLink .= '&right=' . $outputVolumeId;
    $outputLink .= '&jsImports=' . $midasPath.'/modules/pyslicer/public/js/lib/visualize.regOutput.js';
    $outputLinkText = 'View Output';  
    return array( array ('text' => $outputLinkText, 'url' => $outputLink));
    }
    
  function resolveInputsAndOutputs($job)
    {
    $midasPath = Zend_Registry::get('webroot');  
    $inputs = array();
    $outputs = array();
    $jobModel = MidasLoader::loadModel('Job', 'remoteprocessing');
    $relatedItems = $jobModel->getRelatedItems($job);
    foreach($relatedItems as $item)
      {
      if($item->getType() == MIDAS_REMOTEPROCESSING_RELATION_TYPE_INPUT)
        {
        $inputs[] = $item;
        }
      elseif($item->getType() == MIDAS_REMOTEPROCESSING_RELATION_TYPE_OUPUT)
        {
        $outputs[] = $item;
        }
      }
    
    // generate inputs
    $expectedInputs = $this->pipelines[$job->getScript()][MIDAS_PYSLICER_EXPECTED_INPUTS];
    $inputGenerator = $this->pipelines[$job->getScript()][MIDAS_PYSLICER_INPUT_GENERATOR];
    $inputLinks = array();
    if(sizeof($inputs) < $expectedInputs)
      {
      $inputLinks = $this->missingInputs;
      }
    else
      {
      $inputLinks = call_user_func_array(array($this, $inputGenerator), array($job, $inputs, $outputs, $midasPath));
      }
    
    // generate outputs if done
    $expectedOutputs = $this->pipelines[$job->getScript()][MIDAS_PYSLICER_EXPECTED_OUTPUTS];
    $outputGenerator = $this->pipelines[$job->getScript()][MIDAS_PYSLICER_OUTPUT_GENERATOR];
    $outputLinks = array();
    if($job->getStatus() == MIDAS_REMOTEPROCESSING_STATUS_DONE)
      {
      if(sizeof($outputs) < $expectedOutputs)
        {
        $outputLinks = $this->missingOutputs;
        }
      else
        {
        if(sizeof($inputs) < $expectedInputs)
          {
          $outputLinks = $this->missingInputs;  
          }
        else
          {
          $outputLinks = call_user_func_array(array($this, $outputGenerator), array($job, $inputs, $outputs, $midasPath));
          }
        }
      }
    return array('inputs' => $inputLinks, 'outputs' => $outputLinks);
    }
    
  function statuslistAction()
    {
    if(isset($this->userSession->Dao))
      {
      $jobModel = MidasLoader::loadModel('Job', 'remoteprocessing');
      $jobs = $jobModel->getByUser($this->userSession->Dao);
      
      $midasPath = Zend_Registry::get('webroot');
//      $columnsHeaders = array('name' => 'Name', 'script' => 'Job Type', 'params' => 'Params', 'creation_date' => 'Creation Date', 'status' => 'Status', 'output' => 'Output');
      $columnsHeaders = array('name' => 'Name', 'script' => 'Job Type', 'params' => 'Params', 'creation_date' => 'Creation Date', 'status' => 'Status');
      $jobsRows = array();
      $this->view->columnHeaders = $columnsHeaders;
      foreach($jobs as $job)
        {
        $jobRow = array();
        foreach($columnsHeaders as $column => $header)
          {
          if($column === 'name')
            {
            $jobRow['name_string'] = $job->getName();
            $jobRow['name_url'] = $midasPath . '/pyslicer/process/status?jobId='.$job->getJobId();
            }            
          elseif($column === 'status')
            {
            $status = $job->getStatus();
            $jobRow['status_string'] = $this->statusStrings[$status];
            $jobRow['status_class'] = $this->statusClasses[$status];
            }
          /*elseif($column === 'output')
            {
            if($job->getStatus() == MIDAS_REMOTEPROCESSING_STATUS_DONE)
              {
              // TODO get proper redirect URL from job based on job type and params, here
              // hard coding with expectation of segmentation
              $relatedItems = $jobModel->getRelatedItems($job);
              foreach($relatedItems as $item)
                {
                $inputItem = false;
                $outputItem = false;
                $inputItemId = false;
                if($item->getType() == MIDAS_REMOTEPROCESSING_RELATION_TYPE_INPUT)
                  {
                  $inputItemId = $item->getItemId();  
                  }
                elseif($item->getType() == MIDAS_REMOTEPROCESSING_RELATION_TYPE_OUPUT)
                  {
                  $outputItemId = $item->getItemId();  
                  }
                if($inputItemId == false || $outputItemId == false)
                  {
                  $jobRow['output_string'] = 'unknown error';
                  $jobRow['output_url'] = '';
                  $jobRow['output_qtip'] = 'Missing input or output item';
                  }
                else
                  {
                  $url = $midasPath . '/visualize/paraview/slice?itemId='.$inputItemId.'&meshes='.$outputItemId.'&jsImports=/midas/modules/pyslicer/public/js/lib/visualize.meshView.js';
                  $jobRow['output_string'] = 'view output';
                  $jobRow['output_url'] = $url;
                  $jobRow['output_qtip'] = false;
                  }
                }
              }
            elseif($job->getStatus() == MIDAS_PYSLICER_REMOTEPROCESSING_JOB_EXCEPTION)
              {
              // TODO something sensible for the error
              $jobRow['output_string'] = 'TODO: view error output';
              $jobRow['output_url'] = false;
              $jobRow['output_qtip'] = 'TODO: view error';
              }
            else
              {
              // TODO: something with status of running jobs
              $jobRow['output_string'] = 'TODO: view status';
              $jobRow['output_url'] = false;
              $jobRow['output_qtip'] = false;
              }
            }*/
          else
            {
            $jobRow[$column] = $job->get($column);
            }
          }
          $jobRows[] = $jobRow;
        }
      $this->view->jobsRows = $jobRows;
      }
    else
      {
      $this->view->jobsRows = array();  
      }
    }
    
  function statusAction()
    {
    if($this->userSession->Dao == null)
      {
      $this->haveToBeLogged();
      return;
      }
      
      
    $jobId = $this->_getParam('jobId');  
    if(!isset($jobId) || !is_numeric($jobId))
      {
      throw new Zend_Exception('invalid jobId');
      }
    $jobModel = MidasLoader::loadModel("Job", 'remoteprocessing');
    $job = $jobModel->load($jobId);
    if(!$job)
      {
      throw new Zend_Exception('invalid jobId');
      }
  
    $userDao = $this->userSession->Dao;
    if($userDao->getUserId() != $job->getCreator() && !$userDao->getAdmin())
      {
      throw new Zend_Exception('You do not have permissions to view this job.');
      }
    
    $jobstatusModel = MidasLoader::loadModel('Jobstatus', 'pyslicer');
    $jobStatuses = $jobstatusModel->getForJob($job);
      
    $this->view->json['jobId'] = $jobId;
    $this->view->json['statusStrings'] = $this->statusStrings;
    $this->view->json['statusClasses'] = $this->statusClasses;
    $this->view->job = $job;
    $this->view->statusStrings = $this->statusStrings;
    $this->view->statusClasses = $this->statusClasses;
    $this->view->insAndOuts = $this->resolveInputsAndOutputs($job);
    $this->view->jobStatuses = $jobStatuses;
    $this->view->header = 'PySlicer Job Status';
    }  
    
    

  /**
   *   Item Action
   */
  function itemAction()
    {
    // TODO put these paths in the config, once a config exists

    // set these two
    $twistedServerUrl = 'http://localhost:8880/';

    
    // TODO add a check for the user session existing
    $itemId = $this->_getParam('itemId');
    $outputItemName = $this->_getParam('outputItemName');
    
    
    
    if(!isset($itemId) || !is_numeric($itemId))
      {
      throw new Zend_Exception('invalid itemId');
      }

    $itemDao = $this->Item->load($itemId);
    if($itemDao === false)
      {
      throw new Zend_Exception("This item doesn't exist.");
      }
    if(!$this->Item->policyCheck($itemDao, $this->userSession->Dao, MIDAS_POLICY_READ))
      {
      throw new Zend_Exception('You should have read access on this item.');
      }

    // just use the first folder for now
    // TODO where should output of processing go?
    $parentFolders = $itemDao->getFolders();
    $parentFolder = $parentFolders[0];
    
    $userDao = $this->userSession->Dao;
    $userEmail = $userDao->getEmail();
    // get an api key for this user
    $userApiModel = MidasLoader::loadModel('Userapi', 'api');
    $userApiDao = $userApiModel->getByAppAndUser('Default', $userDao);
    if(!$userApiDao)
      {
      throw new Zend_Exception('You need to create a web-api key for this user for application: Default');
      }

    
    $midasPath = Zend_Registry::get('webroot');
    $midasUrl = 'http://' . $_SERVER['HTTP_HOST'] . $midasPath;
    $apiKey = $userApiDao->getApikey();
    $parentFolderId = $parentFolder->getFolderId();

    // TODO probably a security hole to put the email and api key on a cmd line execution, other
    // users of that machine could see them with top/ps
    // similarly with putting in the url
    $slicerjobParams = array($midasUrl, $userEmail, $apiKey, $itemId, $parentFolderId, $outputItemName);
    $requestParams = "";
    foreach ($slicerjobParams as $ind => $param)
      {
      if ($ind < count($slicerjobParams))
        {
        if ($ind > 0)
          {
          $requestParams .= "&";
          }
        $requestParams .= 'slicerjob=' . $param;
        }
      }

    $url = $twistedServerUrl . '?' . $requestParams;
    // TODO what if the url isn't there?  no server?  what do we get back?
    $data = file_get_contents($url);
    // data is false if no server
    // otherwise data is response from call
    if($data === false)
      {
      // redirect to the parent folder
      $this->_redirect('/folder/'.$parentFolderId);
      }
    else
      {
      $dataParts = explode('=', $data);
      $outputItemId = $dataParts[1];
      // redirect to the output item
      $this->_redirect('/item/'.$outputItemId);
      }
    }



}//end class
