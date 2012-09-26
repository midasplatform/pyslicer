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
    $this->addCallBack('CALLBACK_CORE_GET_FOOTER_HEADER', 'getHeader');
    $this->addCallBack('CALLBACK_CORE_ITEM_VIEW_ACTIONMENU', 'getItemMenuLink');
    $this->addCallBack('CALLBACK_CORE_GET_LEFT_LINKS', 'getLeftLink');
    $this->addCallBack('CALLBACK_CORE_GET_FOOTER_LAYOUT', 'getFooter');
    }

  /** get layout header */
  public function getHeader()
    {
    return '<link type="text/css" rel="stylesheet" href="'.Zend_Registry::get('webroot').'/modules/'.$this->moduleName.'/public/css/layout/'.$this->moduleName.'.css" />';
    }

  /** get layout footer */
  public function getFooter()
    {
    $footer = '<script type="text/javascript" src="'.Zend_Registry::get('webroot').'/modules/api/public/js/common/common.ajaxapi.js"></script>';
    $footer .= '<script type="text/javascript" src="'.Zend_Registry::get('webroot').'/modules/'.$this->moduleName.'/public/js/layout/'.$this->moduleName.'.js"></script>';
    return $footer;
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
    
  /**
   *@method getLeftLink
   * will generate a link for this module to be displayed in the main view.
   */
  public function getLeftLink()
    {
    $fc = Zend_Controller_Front::getInstance();
    $baseURL = $fc->getBaseUrl();
    $moduleWebroot = $baseURL . '/'.$this->moduleName;

    
    if(isset($this->userSession->Dao))
      {
      $apiComponent = MidasLoader::loadComponent('Api', $this->moduleName);
      $args = array("useSession" => true);
      $jobCounts = $apiComponent->getUserJobCountsByStatus($args);
      $jobsCounts = '</span><span id="midas_'.$this->moduleName.'_jobcount_wait">' . $jobCounts['wait'] .
                    '</span><span id="midas_'.$this->moduleName.'_jobcount_started">' . $jobCounts['started'] .
                    '</span><span id="midas_'.$this->moduleName.'_jobcount_done">' . $jobCounts['done'] .
                    '</span><span id="midas_'.$this->moduleName.'_jobcount_error">' . $jobCounts['error'] . '</span>';
      return array('Jobs '. $jobsCounts => array($moduleWebroot . '/process/status',  $baseURL . '/modules/'.$this->moduleName.'/public/images/slicer_icon16x16.png'));
      }
    else
      {
      return array();    
      }
    }

    
} //end class
?>