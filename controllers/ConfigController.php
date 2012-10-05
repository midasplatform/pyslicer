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

/** Config controller for the pyslicer module */
class Pyslicer_ConfigController extends Pyslicer_AppController
{
  public $_models = array('Setting');
  public $_moduleModels = array();

  /** Main module configuration page */
  function indexAction()
    {
    $this->requireAdminPrivileges();
    $slicerProxyUrl = $this->Setting->getValueByName('slicerProxyUrl', 'pyslicer');
    if(!$slicerProxyUrl)
      {
      $slicerProxyUrl = '';
      }
    $this->view->slicerProxyUrl = $slicerProxyUrl;

    if($this->_request->isPost())
      {
      $this->disableLayout();
      $this->disableView();
      $submitConfig = $this->_getParam('submitConfig');
      $slicerProxyUrl = $this->_getParam('slicerProxyUrl');
      if(isset($submitConfig))
        {
        $this->Setting->setConfig('slicerProxyUrl', $slicerProxyUrl, 'pyslicer');
        echo JsonComponent::encode(array('status' => 'ok', 'message' => 'Changes saved'));
        }
      }
    }

}//end class

