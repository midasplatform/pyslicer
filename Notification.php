<?php
/** notification manager*/
class Pyslicer_Notification extends MIDAS_Notification
  {
  public $moduleName = 'pyslicer';

  /** Register callbacks */
  public function init()
    {
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
    if($itemModel->policyCheck($item, null, MIDAS_POLICY_READ) ||
       isset($this->userSession->Dao) && $itemModel->policyCheck($item, $this->userSession->Dao, MIDAS_POLICY_READ))
      {
      $webroot = Zend_Controller_Front::getInstance()->getBaseUrl();
      return '<li><a href="'.$webroot.'/'.$this->moduleName.'/process/item?itemId='.$params['item']->getKey().
             '"><img alt="" src="'.$webroot.'/modules/'.$this->moduleName.'/public/images/slicer_icon16x16.png" /> Process Item in Slicer</a></li>';
      }
    else
      {
      return null;  
      }
    }

} //end class
?>

