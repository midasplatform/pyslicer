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
/** Jobstatus Model*/
class Pyslicer_JobstatusModelBase extends Pyslicer_AppModel
{
  /** construct */
  public function __construct()
    {
    parent::__construct();
    $this->_name = 'pyslicer_jobstatus';
    $this->_key = 'jobstatus_id';

    $this->_mainData = array(
        'jobstatus_id' =>  array('type' => MIDAS_DATA),
        'remoteprocessing_job_id' =>  array('type' => MIDAS_DATA),
        'event_id' =>  array('type' => MIDAS_DATA),
        'notify_date' =>  array('type' => MIDAS_DATA),
        'event_type' =>  array('type' => MIDAS_DATA),
        'message' =>  array('type' => MIDAS_DATA),
        'job' =>  array('type' => MIDAS_MANY_TO_ONE, 'module' => 'remoteprocessing', 'model' => 'Job', 'parent_column' => 'remoteprocessing_job_id', 'child_column' => 'job_id'),
        );
    $this->initialize(); // required
    } // end __construct()


} // end class Pyslicer_JobstatusModelBase
