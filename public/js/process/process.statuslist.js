$(window).load(function () {
    $('a.paramsLink').click(function () {
        midas.showDialogWithContent('Job Parameters', $(this).attr('qtip'), false);
    });
        

    $('a#segmentation').click(function() {
        midas.loadDialog("selectitem_volumeRendering","/browse/selectitem");
        midas.showDialog('Browse for the Image to be Segmented');

        midas.pyslicer.index.itemSelectionCallback = function(name, id) {
            var redirectUrl = $('.webroot').val() + '/visualize/paraview/slice?itemId=' + id;
            redirectUrl += '&operations=pointSelect&jsImports=' + $('.webroot').val() + '/modules/pyslicer/public/js/lib/visualize.pointSelect.js';
            window.location = redirectUrl;
        };
    });
    
    
    $('a#registration').click(function() {
        midas.loadDialog("selectitem_registration_fixed","/browse/selectitem");
        midas.showDialog('Browse for the Registration Fixed Image');

        midas.pyslicer.index.itemSelectionCallback = function(name, fixedId) {
            midas.loadDialog("selectitem_registration_moving","/browse/selectitem");
            midas.showDialog('Browse for the Registration Moving Image');

            midas.pyslicer.index.itemSelectionCallback = function(name, movingId) {
                var redirectUrl = $('.webroot').val() + '/visualize/paraview/dual?left=' + fixedId;
                redirectUrl += '&right=' + movingId + '&operations=pointMap&jsImports=' + $('.webroot').val() + '/modules/pyslicer/public/js/lib/visualize.landmarkRegistration.js';
                window.location = redirectUrl;
            };
        };
    });

});
