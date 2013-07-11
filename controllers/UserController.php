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

/** User settings management */
class Pyslicer_UserController extends Pyslicer_AppController
{
  public $_models = array('User');
  public $_moduleModels = array('User');

  /**
   * Shows this user's default settings for Pyslicer module
   * @param useAjax If this is an Ajax call
   * @param userId userId Id of the user.  Must be session user itself.
   * @param pipeline Pipeline name.
   */
  function indexAction()
    {
    $this->disableLayout();
    $useAjax = $this->_getParam('useAjax');

    $userDao = Zend_Registry::get('userSession')->Dao;
    $userId = $this->_getParam('userId');
    if(isset($userId))
      {
      $userDao = $this->User->load($userId);
      }

    if(!$userDao)
      {
      throw new Zend_Exception('Invalid userId', 404);
      }
    if(!$this->logged)
      {
      throw new Zend_Exception('Must be logged in', 403);
      }
    $pipeline = $this->_getParam('pipeline');
    if(!isset($pipeline))
      {
      $pipeline = MIDAS_PYSLICER_PDF_SEGMENTATION_PIPELINE;
      }

    $pyslicerUserDao = $this->Pyslicer_User->getByUser($userDao, $pipeline);
    if (isset($useAjax) && $useAjax == true)
      {
      $this->disableView();
      $pyslicerUserArr = array();
      if ($pyslicerUserDao)
        {
        $pyslicerUserArr = $pyslicerUserDao->toArray();
        }
      echo JsonComponent::encode(array('status' => 'ok', 'message' => 'Get Pyslicer User settings', 'pyslicerUser' => $pyslicerUserArr));
      }
    else
      {
      $this->view->pyslicerUser = $pyslicerUserDao;
      }
    }

  /**
   * Create folders for the given pipeline or return existing folders if rootFolderId are same.
   * @param userId Id of the user.  Must be session user itself.
   * @param rootFolderId root folder id for the given pipeline.
   * @param pipeline Pipeline name.
   */
  function createfoldersAction()
    {
    $this->disableLayout();
    $this->disableView();

    $rootFolderId = $this->_getParam('rootFolderId');
    $userId = $this->_getParam('userId');
    $userDao = Zend_Registry::get('userSession')->Dao;
    if(isset($userId))
      {
      $userDao = $this->User->load($userId);
      }
    if(!$userDao)
      {
      throw new Zend_Exception('Invalid userId', 400);
      }
    if(!$this->logged)
      {
      throw new Zend_Exception('Must be logged in', 401);
      }

    $pipeline = $this->_getParam('pipeline');
    if(!isset($pipeline))
      {
      $pipeline = MIDAS_PYSLICER_PDF_SEGMENTATION_PIPELINE;
      }
    $pyslicerUserDao = $this->Pyslicer_User->createFolders($userDao, $rootFolderId, $pipeline);
    echo JsonComponent::encode(array('status' => 'ok', 'message' => 'Folders created', 'pyslicerUser' => $pyslicerUserDao));
    }

  /**
   * Delete default Pyslicer settings for this user
   * @param userId Id of the user.  Must be session user itself.
   * @param pipeline Pipeline name.
   */
  function deleteAction()
    {
    $this->disableLayout();
    $this->disableView();

    $userId = $this->_getParam('userId');
    $userDao = Zend_Registry::get('userSession')->Dao;
    if(isset($userId))
      {
      $userDao = $this->User->load($userId);
      }
    if(!$userDao)
      {
      throw new Zend_Exception('Invalid userId', 400);
      }
    if(!$this->logged)
      {
      throw new Zend_Exception('Must be logged in', 401);
      }
    $pipeline = $this->_getParam('pipeline');
    if(!isset($pipeline))
      {
      $pipeline = MIDAS_PYSLICER_PDF_SEGMENTATION_PIPELINE;
      }

    $pyslicerUserDao = $this->Pyslicer_User->getByUser($userDao, $pipeline);
    if ($pyslicerUserDao)
      {
      $this->Pyslicer_User->delete($pyslicerUserDao);
      }
    echo JsonComponent::encode(array('status' => 'ok', 'message' => 'No default Folders.'));
    }
  } // end class
?>
