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
   * @param token Authentication token
   * @param item_id The id of the item to be processed
   * @param output_item_name The name of the created output item
   * @param seed The x,y,z point coords of the seed point
   * @param output_folder_id (optional) The id of the folder where the output item
     will be created, if not supplied, the first parent folder found on the input
     item will be used as the output folder.
   * @return TODO for now data from response.
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
    $seed = $args['seed'];

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

    $midasPath = Zend_Registry::get('webroot');
    $midasUrl = 'http://' . $_SERVER['HTTP_HOST'] . $midasPath;
    $apiKey = $userApiDao->getApikey();
    $parentFolderId = $parentFolder->getFolderId();

    // TODO probably a security hole to put the email and api key in the url
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

    // TODO store remote processing job info
    $jobModel = MidasLoader::loadModel('Job', 'remoteprocessing');
    $job = MidasLoader::newDao('JobDao', 'remoteprocessing');
    $job->setCreatorId($userDao->getUserId());
    $job->setStatus(MIDAS_REMOTEPROCESSING_STATUS_WAIT);
    // TODO script, params, name
    $jobModel->save($job);    
    $jobModel->addItemRelation($job, $itemDao, MIDAS_REMOTEPROCESSING_RELATION_TYPE_INPUT);
    
    
    // TODO store twisted server url in config
    $twistedServerUrl = 'http://localhost:8880/';
    $url = $twistedServerUrl . '?' . $requestParams;
    // TODO what if the url isn't there?  no server?  what do we get back?
    // we get back false, and should take some appropriate action for the
    // return value here
    $data = file_get_contents($url);  
      
    // TODO some better return value
    return $data;
    }

} // end class




