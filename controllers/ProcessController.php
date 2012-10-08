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
  public $_moduleComponents = array('Pipeline');
  public $_models = array('Item', 'Folder');
  
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
    $this->view->json['statusStrings'] = $this->ModuleComponent->Pipeline->statusStrings;
    $this->view->json['statusClasses'] = $this->ModuleComponent->Pipeline->statusClasses;
    $this->view->json['jobStatusesCount'] = sizeof($jobStatuses);
    $this->view->json['jobStatus'] = $job->getStatus();
    
    $this->view->job = $job;
    $this->view->statusStrings = $this->ModuleComponent->Pipeline->statusStrings;
    $this->view->statusClasses = $this->ModuleComponent->Pipeline->statusClasses;
    $this->view->insAndOuts = $this->ModuleComponent->Pipeline->resolveInputsAndOutputs($job);
    $this->view->jobConditionLines = $this->ModuleComponent->Pipeline->formatJobCondition($job->getCondition());
    $this->view->jobStatuses = $jobStatuses;
    }  



}//end class
