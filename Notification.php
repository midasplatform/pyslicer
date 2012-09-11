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
    if(isset($this->userSession->Dao))
      {
      $webroot = Zend_Controller_Front::getInstance()->getBaseUrl();
      return '<li><a href="'.$webroot.'/visualize/paraview/slice?itemId='.$item->getKey().
             '&operations=pointSelect&jsImports=/midas/modules/'.$this->moduleName.'/public/js/lib/visualize.pointSelect.js">'.
             '<img alt="" src="'.$webroot.'/modules/'.$this->moduleName.'/public/images/slicer_icon16x16.png" /> '.
             'Region Growing Segmentation</a></li>';
      }
    else
      {
      return null;  
      }
    }
    
} //end class
?>

