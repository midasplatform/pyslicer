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

  /**
   *   Item Action
   */
  function itemAction()
    {
    // TODO put these paths in the config, once a config exists
      
    $slicerPath = 'FILL_IN';
    $workDirRoot = 'FILL_IN';

    $script = $workDirRoot . 'quick.py';
    $scriptOut = $workDirRoot . 'quick.out';
    $scriptErr = $workDirRoot . 'quick.err';
    $xvfbLog = $workDirRoot . 'xvfb.log';
    
    $slicerPathArgs = 'xvfb-run -a -e '.$xvfbLog.' '.$slicerPath.' --no-main-window --python-script';
    $linuxAsync = '> '.$scriptOut.' 2>'.$scriptErr.' &';
    //$linuxAsync = '> /dev/null 2>/dev/null &';
    
      
      
      
    $itemId = $this->_getParam('itemId');
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
    
    // just try to exec for now
    $output = array();
    $returnVar;
    
    // programmatically get
    // slicer path
    // script to run
    // url of midas
    // email of user
    // api_key of user
    // input item id
    // output item parent folder id
    
    
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
    $url = 'http://' . $_SERVER['HTTP_HOST'] . $midasPath;
    $apiKey = $userApiDao->getApikey();
    $parentFolderId = $parentFolder->getFolderId();
    
    $scriptArgs = implode(' ', array($script, $url, $userEmail, $apiKey, $itemId, $parentFolderId));
    
    $cmd = implode(' ', array($slicerPathArgs, $scriptArgs, $linuxAsync));
    
    // TODO probably a security hole to put the email and api key on a cmd line execution, other
    // users of that machine could see them with top/ps
    exec($cmd, $output, $returnVar);
    
    // redirect to the parent folder
    $this->_redirect('/folder/'.$parentFolderId);
    }



}//end class
