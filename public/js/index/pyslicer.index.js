var midas = midas || {};
midas.pyslicer = midas.pyslicer || {};
midas.pyslicer.index = midas.pyslicer.index || {};

$(document).ready(function(){

    $('a.volumeRendering').click(function() {
        midas.loadDialog("selectitem_volumeRendering","/browse/selectitem");
        midas.showDialog('Browse for the Image to be Volume Rendered');

        midas.pyslicer.index.itemSelectionCallback = function(name, id) {
            var redirectUrl = $('.webroot').val() + '/pvw/paraview/volume?itemId=' + id;
            window.location = redirectUrl;
        };
    });

    $('a.segmentation').click(function() {
        midas.loadDialog("selectitem_volumeRendering","/browse/selectitem");
        midas.showDialog('Browse for the Image to be Segmented');

        midas.pyslicer.index.itemSelectionCallback = function(name, id) {
            var redirectUrl = $('.webroot').val() + '/pvw/paraview/slice?itemId=' + id;
            redirectUrl += '&operations=pointSelect&jsImports=' + $('.webroot').val() + '/modules/pyslicer/public/js/lib/pvw.pointSelect.js';
            window.location = redirectUrl;
        };
    });

});

itemSelectionCallback = function(name, id)  {
  midas.pyslicer.index.itemSelectionCallback(name, id);
  return;
}