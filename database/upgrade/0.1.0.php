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

class Pyslicer_Upgrade_0_1_0 extends MIDASUpgrade
{
  public function mysql()
    {
    $this->db->query("CREATE TABLE IF NOT EXISTS `pyslicer_user` (
                     `pyslicer_user_id` bigint(20) NOT NULL AUTO_INCREMENT,
                     `user_id` bigint(20) NOT NULL,
                     `pipeline` varchar(255) NOT NULL,
                     `root_folder_id` bigint(20) NOT NULL,
                     `data_folder_id` bigint(20) NULL DEFAULT NULL,
                     `preset_folder_id` bigint(20) NULL DEFAULT NULL,
                     `output_folder_id` bigint(20) NULL DEFAULT NULL,
                     PRIMARY KEY (`pyslicer_user_id`)
                     )");
    }
}
?>
