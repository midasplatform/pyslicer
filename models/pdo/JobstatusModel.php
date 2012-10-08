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

require_once BASE_PATH.'/modules/pyslicer/models/base/JobstatusModelBase.php';

/** jobstatus model */
class Pyslicer_JobstatusModel extends Pyslicer_JobstatusModelBase
{

  /** get jobstatus rows related to this job, in order of event_id */
  function getForJob($job)
    {
    if(!$job instanceof Remoteprocessing_JobDao)
      {
      throw new Zend_Exception("getForJob should be a Remoteprocessing_Job.");
      }

    $sql = $this->database->select()
          ->from('pyslicer_jobstatus')
          ->setIntegrityCheck(false)
          ->where('remoteprocessing_job_id = ?', $job->getKey())
          ->order('event_id ASC');

    $rowset = $this->database->fetchAll($sql);
    $return = array();
    foreach($rowset as $row)
      {
      $jobstatusDao = $this->initDao('Jobstatus', $row, 'pyslicer');
      $return[] = $jobstatusDao; 
      }
    return $return;
    }

}  // end class