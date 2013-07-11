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
/** User Model*/
abstract class Pyslicer_UserModelBase extends Pyslicer_AppModel
{
  /** construct */
  public function __construct()
    {
    parent::__construct();
    $this->_name = 'pyslicer_user';
    $this->_daoName = 'UserDao';
    $this->_key = 'pyslicer_user_id';

    $this->_mainData = array(
        'pyslicer_user_id' =>  array('type' => MIDAS_DATA),
        'user_id' => array('type' => MIDAS_ONE_TO_ONE, 'model' => 'User', 'parent_column' => 'user_id', 'child_column' => 'user_id'),
        'pipeline' =>  array('type' => MIDAS_DATA),
        'root_folder_id' =>  array('type' => MIDAS_DATA),
        'data_folder_id' =>  array('type' => MIDAS_DATA),
        'preset_folder_id' =>  array('type' => MIDAS_DATA),
        'output_folder_id' =>  array('type' => MIDAS_DATA)
        );
    $this->initialize(); // required
    } // end __construct()

  public abstract function deleteByUser($userDao, $pipeline);
  public abstract function getByUser($userDao, $pipeline);

  /**
   * Helper function to create a child folder or use the existing one if it has the same name.
   * @param type $userDao
   * @param type $parentId parent folder Id
   * @param type $name name of the child folder to be created
   * @param type $description description of the child folder to be created
   * @return id of newly created folder or the exsisting folder with the same name
   * @throws Exception
   */
  private function _createChildFolder($userDao, $parentId, $name, $description='')
    {
    if($userDao == false)
      {
      throw new Exception('Cannot create folder anonymously', MIDAS_INVALID_POLICY);
      }
    $folderModel = MidasLoader::loadModel('Folder');
    $record = false;
    $uuid = '';
    if($parentId == -1) //top level user folder being created
      {
      $new_folder = $folderModel->createFolder($name, $description, $userDao->getFolderId(), $uuid);
      }
    else //child of existing folder
      {
      $folder = $folderModel->load($parentId);
      if(($existing = $folderModel->getFolderExists($name, $folder)))
        {
        $returnArray = $existing->toArray();
        return $returnArray['folder_id'];
        }
      $new_folder = $folderModel->createFolder($name, $description, $folder, $uuid);
      if($new_folder === false)
        {
        throw new Exception('Create folder failed', MIDAS_INTERNAL_ERROR);
        }
      $policyGroup = $folder->getFolderpolicygroup();
      $policyUser = $folder->getFolderpolicyuser();
      $folderpolicygroupModel = MidasLoader::loadModel('Folderpolicygroup');
      $folderpolicyuserModel = MidasLoader::loadModel('Folderpolicyuser');
      foreach($policyGroup as $policy)
        {
        $folderpolicygroupModel->createPolicy($policy->getGroup(), $new_folder, $policy->getPolicy());
        }
      foreach($policyUser as $policy)
        {
        $folderpolicyuserModel->createPolicy($policy->getUser(), $new_folder, $policy->getPolicy());
        }
      if(!$folderModel->policyCheck($new_folder, $userDao, MIDAS_POLICY_ADMIN))
        {
        $folderpolicyuserModel->createPolicy($userDao, $new_folder, MIDAS_POLICY_ADMIN);
        }
      }
    // reload folder to get up to date privacy status
    $new_folder = $folderModel->load($new_folder->getFolderId());
    $returnArray = $new_folder->toArray();
    return $returnArray['folder_id'];
    }

  /**
   * Create folders for a given pipeline or return existing folders if rootFolderId are same.
   * @param userDao The core user
   * @param rootFolderId The id of the root folder.
   * @return The pyslicer user dao that was created
   */
  public function createFolders($userDao, $rootFolderId, $pipeline=MIDAS_PYSLICER_PDF_SEGMENTATION_PIPELINE)
    {
    if(!$userDao)
      {
      throw new Exception('Anonymous users may not create folders.', MIDAS_PYSLICER_INVALID_POLICY);
      }
    $folderModel = MidasLoader::loadModel('Folder');
    // Check input root folder
    $rootFolderDao = $folderModel->load($rootFolderId);
    if($rootFolderDao === false)
      {
      throw new Zend_Exception('This folder does not exist.', MIDAS_PYSLICER_INVALID_PARAMETER);
      }
    if(!$folderModel->policyCheck($rootFolderDao, $userDao, MIDAS_POLICY_WRITE))
      {
      throw new Zend_Exception('Write access on this folder required.', MIDAS_PYSLICER_INVALID_POLICY);
      }

    $existingPyslicerUserDao = $this->getByUser($userDao, $pipeline);
    if ($existingPyslicerUserDao) {
      // return existing one if rootFolderId are same
      if ($existingPyslicerUserDao->getRootFolderId() == $rootFolderId)
        {
        return $existingPyslicerUserDao;
        }
      else
        {
        // every user can only have at most one set of default folders
        $this->deleteByUser($userDao, $pipeline);
        }
    }
    $pyslicerUserDao = MidasLoader::newDao('UserDao', 'pyslicer');
    $pyslicerUserDao->setUserId($userDao->getKey());
    $pyslicerUserDao->setPipeline($pipeline);
    $pyslicerUserDao->setRootFolderId($rootFolderId);
    $dataFolderId = $this->_createChildFolder($userDao, $rootFolderId, 'data', 'input data directory');
    $pyslicerUserDao->setDataFolderId($dataFolderId);
    $presetFolderId = $this->_createChildFolder($userDao, $rootFolderId, 'presets', 'parameter preset directory');
    $pyslicerUserDao->setPresetFolderId($presetFolderId);
    $outputFolderId = $this->_createChildFolder($userDao, $rootFolderId, 'output', 'output results directory');
    $pyslicerUserDao->setOutputFolderId($outputFolderId);
    $this->save($pyslicerUserDao);
    return $pyslicerUserDao;
    }

} // end class Pyslicer_UserModelBase
