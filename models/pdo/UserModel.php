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

require_once BASE_PATH.'/modules/pyslicer/models/base/UserModelBase.php';

/**
 * Pyslicer user pdo model
 */
class Pyslicer_UserModel extends Pyslicer_UserModelBase
{

  /**
   * Delete an pyslicer_user corresponding to the core user.
   * @param userDao The core
   * @param pipeline Pipeline name.
   */
  public function deleteByUser($userDao, $pipeline)
    {
    $this->database->getDB()->delete('pyslicer_user', array(
      'user_id = ?' => $userDao->getKey(),
      'pipeline = ?' => $pipeline
      ));
    }

  /**
   * Returns the pyslicer_user corresponding to the core user, or false if the
   * user is not an pyslicer_user.
   * @param userDao The core user
   * @param pipeline Pipeline name.
   */
  public function getByUser($userDao, $pipeline)
    {
    $sql = $this->database->select()
          ->where('user_id = ?', $userDao->getKey())
          ->where('pipeline = ?', $pipeline);
    $row = $this->database->fetchRow($sql);
    $dao = $this->initDao('User', $row, 'pyslicer');
    if($dao)
      {
      return $dao;
      }
    else
      {
      return false;
      }
    }
}
