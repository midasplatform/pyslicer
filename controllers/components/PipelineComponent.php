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


/** Component for dealing with pipelines */
class Pyslicer_PipelineComponent extends AppComponent
{

  public $statusStrings =
    array(MIDAS_REMOTEPROCESSING_STATUS_WAIT => 'starting',
          MIDAS_REMOTEPROCESSING_STATUS_STARTED => 'running',
          MIDAS_REMOTEPROCESSING_STATUS_DONE => 'complete',
          MIDAS_PYSLICER_REMOTEPROCESSING_JOB_EXCEPTION => 'error');
  public $statusClasses =
    array(MIDAS_REMOTEPROCESSING_STATUS_WAIT => 'midas_pyslicer_wait',
          MIDAS_REMOTEPROCESSING_STATUS_STARTED => 'midas_pyslicer_started',
          MIDAS_REMOTEPROCESSING_STATUS_DONE => 'midas_pyslicer_done',
          MIDAS_PYSLICER_REMOTEPROCESSING_JOB_EXCEPTION => 'midas_pyslicer_error');
  
  protected $pipelines =
    array(
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
  
  protected $missingInputs = array( array ('text' => 'Error: missing input', 'url' => ''));
  protected $missingOutputs = array( array ('text' => 'Error: missing output', 'url' => ''));
  
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
    
  public function resolveInputsAndOutputs($job)
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
    
    
  public function formatJobCondition($condition)
    {
    $splitLines = array();
    if(isset($condition) && $condition != '')
      {
      $condition = ltrim($condition, "['");
      $condition = rtrim($condition, "']");
      $errorLines = explode("', '", $condition);
      foreach($errorLines as $errorLine)
        {
        $lines = explode("\\n", $errorLine);
        $splitLines = array_merge($splitLines, $lines);
        }
    }
    return $splitLines;
  }
    
} // end class




