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

  /** init method */
  function init()
    {
    }
    
  function statusAction()
    {
    if(isset($this->userSession->Dao))
      {
      $jobModel = MidasLoader::loadModel('Job', 'remoteprocessing');
      $jobs = $jobModel->findBy('creator_id', $this->userSession->Dao->getKey());
      
      $midasPath = Zend_Registry::get('webroot');
      $columnsHeaders = array('name' => 'Name', 'script' => 'Job Type', 'params' => 'Params', 'creation_date' => 'Creation Date', 'status' => 'Status', 'output' => 'Output');
      $statusStrings =
          array(MIDAS_REMOTEPROCESSING_STATUS_WAIT => 'waiting',
                MIDAS_REMOTEPROCESSING_STATUS_STARTED => 'started',
                MIDAS_REMOTEPROCESSING_STATUS_DONE => 'done',
                MIDAS_PYSLICER_REMOTEPROCESSING_JOB_EXCEPTION => 'error');
      $statusClasses =
          array(MIDAS_REMOTEPROCESSING_STATUS_WAIT => 'midas_pyslicer_wait',
                MIDAS_REMOTEPROCESSING_STATUS_STARTED => 'midas_pyslicer_started',
                MIDAS_REMOTEPROCESSING_STATUS_DONE => 'midas_pyslicer_done',
                MIDAS_PYSLICER_REMOTEPROCESSING_JOB_EXCEPTION => 'midas_pyslicer_error');
      $jobsRows = array();
      $this->view->columnHeaders = $columnsHeaders;
      foreach($jobs as $job)
        {
        $jobRow = array();
        foreach($columnsHeaders as $column => $header)
          {
          if($column === 'status')
            {
            $status = $job->getStatus();
            $jobRow['status_string'] = $statusStrings[$status];
            $jobRow['status_class'] = $statusClasses[$status];
            }
          elseif($column === 'output')
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
            }
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
