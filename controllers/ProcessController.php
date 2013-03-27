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
    if($this->userSession->Dao == null)
      {
      $this->haveToBeLogged();
      return;
      }  
      
    if(isset($this->userSession->Dao))
      {
      $jobModel = MidasLoader::loadModel('Job', 'remoteprocessing');
      $jobs = $jobModel->getByUser($this->userSession->Dao);
      
      $midasPath = Zend_Registry::get('webroot');
      $columnsHeaders = array('name' => 'Name', 'script' => 'Job Type', 'params' => 'Params', 'creation_date' => 'Creation Date', 'status' => 'Status');
      $jobRows = array();
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
            $jobRow['status_string'] = $this->ModuleComponent->Pipeline->statusStrings[$status];
            $jobRow['status_class'] = $this->ModuleComponent->Pipeline->statusClasses[$status];
            }
          else
            {
            $jobRow[$column] = $job->get($column);
            }
          }
          $jobRows[] = $jobRow;
        }
      $this->view->jobsRows = $jobRows;
      $this->view->header = "Slicer Pipelines";
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
    $this->view->header = 'Slicer Job Status';
    }  



}//end class
