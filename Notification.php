<?php

require_once BASE_PATH . '/modules/api/library/APIEnabledNotification.php';

/** notification manager*/
class Pyslicer_Notification extends ApiEnabled_Notification
  {
  public $moduleName = 'pyslicer';
  public $_moduleComponents=array('Api');
  
  
  /** Register callbacks */
  public function init()
    {
    $this->enableWebAPI($this->moduleName);  
    $fc = Zend_Controller_Front::getInstance();
    $this->moduleWebroot = $fc->getBaseUrl().'/modules/'.$this->moduleName;
    $this->coreWebroot = $fc->getBaseUrl().'/core';
    $this->addCallBack('CALLBACK_CORE_ITEM_VIEW_JS', 'getItemViewJs');
    $this->addCallBack('CALLBACK_CORE_ITEM_VIEW_ACTIONMENU', 'getItemMenuLink');
    }

  /** Get the link to place in the item action menu */
  public function getItemMenuLink($params)
    {
    $item = $params['item'];
    $revisions = $item->getRevisions();
    if(count($revisions) === 0)
      {
      return null;
      }
    $itemModel = MidasLoader::loadModel('Item');
    if(isset($this->userSession->Dao) && $itemModel->policyCheck($item, $this->userSession->Dao, MIDAS_POLICY_READ))
      {
      $webroot = Zend_Controller_Front::getInstance()->getBaseUrl();
      return '<li><a id="pyslicerProcessItem" href="javascript:;"' .
          //'.$webroot.'/'.$this->moduleName.'/process/item?itemId='.$params['item']->getKey().
             '><img alt="" src="'.$webroot.'/modules/'.$this->moduleName.'/public/images/slicer_icon16x16.png" /> Process Item in Slicer</a></li>';
      }
    else
      {
      return null;  
      }
    }
    
  /** Get javascript for the item view */
  public function getItemViewJs($params)
    {
    return array($this->moduleWebroot.'/public/js/common/common.pyslicer.js');
    return array($this->apiWebroot.'/public/js/common/common.ajaxapi.js');
    }
    
} //end class
?>

