var midas = midas || {};
midas.pyslicer = midas.pyslicer || {};
midas.pyslicer.index = midas.pyslicer.index || {};

$(document).ready(function(){

    $('a.volumeRendering').click(function() {
        midas.loadDialog("selectitem_volumeRendering","/browse/selectitem");
        midas.showDialog('Browse for the Image to be Volume Rendered');

        midas.pyslicer.index.itemSelectionCallback = function(name, id) {
            var redirectUrl = $('.webroot').val() + '/visualize/paraview/volume?itemId=' + id;
            window.location = redirectUrl;
        };
    });

    $('a.segmentation').click(function() {
        midas.loadDialog("selectitem_volumeRendering","/browse/selectitem");
        midas.showDialog('Browse for the Image to be Segmented');

        midas.pyslicer.index.itemSelectionCallback = function(name, id) {
            var redirectUrl = $('.webroot').val() + '/visualize/paraview/slice?itemId=' + id;
            redirectUrl += '&operations=pointSelect&jsImports=' + $('.webroot').val() + '/modules/pyslicer/public/js/lib/visualize.pointSelect.js';
            window.location = redirectUrl;
        };
    });

    $('a.registration').click(function() {
        midas.loadDialog("selectitem_registration_fixed","/browse/selectitem");
        midas.showDialog('Browse for the Registration Fixed Image');

        midas.pyslicer.index.itemSelectionCallback = function(name, fixedId) {
            midas.loadDialog("selectitem_registration_moving","/browse/selectitem");
            midas.showDialog('Browse for the Registration Moving Image');

            midas.pyslicer.index.itemSelectionCallback = function(name, movingId) {
                console.log("movingSelected");
                var redirectUrl = $('.webroot').val() + '/visualize/paraview/dual?left=' + fixedId;
                redirectUrl += '&right=' + movingId + '&operations=pointMap&jsImports=/midas/modules/pyslicer/public/js/lib/visualize.landmarkRegistration.js';
                window.location = redirectUrl;
            };
        };
    });

});

itemSelectionCallback = function(name, id)  {
  midas.pyslicer.index.itemSelectionCallback(name, id);
  return;
}