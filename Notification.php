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
      $text = 'Slicer';
      return array($text => array($moduleWebroot . '/process/statuslist',  $baseURL . '/modules/'.$this->moduleName.'/public/images/slicer_icon16x16.png'));
      }
    else
      {
      return array();    
      }
    }

    
} //end class
?>
