var midas = midas || {};
midas.pyslicer = midas.pyslicer || {};
midas.pyslicer.statuslist = midas.pyslicer.statuslist || {};


$(document).ready(function(){

    $('a.paramsLink').click(function () {
        midas.showDialogWithContent('Job Parameters', $(this).attr('qtip'), false);
    });

    $('a#segmentation').click(function() {
        midas.loadDialog("selectitem_volumeRendering","/browse/selectitem");
        midas.showDialog('Browse for the Image to be Segmented');

        midas.pyslicer.statuslist.itemSelectionCallback = function(name, id) {
            var redirectUrl = $('.webroot').val() + '/pvw/paraview/slice?itemId=' + id;
            redirectUrl += '&operations=pointSelect&jsImports=' + $('.webroot').val() + '/modules/pyslicer/public/js/lib/pvw.pointSelect.js';
            window.location = redirectUrl;
        };
    });


    $('a#registration').click(function() {
        midas.loadDialog("selectitem_registration_fixed","/browse/selectitem");
        midas.showDialog('Browse for the Registration Fixed Image');

        midas.pyslicer.statuslist.itemSelectionCallback = function(name, fixedId) {
            midas.loadDialog("selectitem_registration_moving","/browse/selectitem");
            midas.showDialog('Browse for the Registration Moving Image');

            midas.pyslicer.statuslist.itemSelectionCallback = function(name, movingId) {
                var redirectUrl = $('.webroot').val() + '/visualize/paraview/dual?left=' + fixedId;
                redirectUrl += '&right=' + movingId + '&operations=pointMap&jsImports=' + $('.webroot').val() + '/modules/pyslicer/public/js/lib/visualize.landmarkRegistration.js';
                window.location = redirectUrl;
            };
        };
    });

    $('a#pdfsegmentation').click(function() {
        midas.loadDialog("selectitem_volumeRendering","/browse/selectitem");
        midas.showDialog('Browse for the Image to be Segmented');

        midas.pyslicer.statuslist.itemSelectionCallback = function(name, id) {
            var redirectUrl = $('.webroot').val() + '/pvw/paraview/slice?itemId=' + id;
            redirectUrl += '&operations=paint&jsImports=' + $('.webroot').val() + '/modules/pyslicer/public/js/lib/pvw.paint.js';
            window.location = redirectUrl;
        };
    });

});

itemSelectionCallback = function(name, id)  {
  midas.pyslicer.statuslist.itemSelectionCallback(name, id);
  return;
}