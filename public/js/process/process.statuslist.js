var midas = midas || {};
midas.pyslicer = midas.pyslicer || {};
midas.pyslicer.statuslist = midas.pyslicer.statuslist || {};

midas.pyslicer.statuslist.pdfSegmenterRootFolderId = '';
midas.pyslicer.statuslist.pdfSegmenterDataFolderId = '';
midas.pyslicer.statuslist.pdfSegmenterPresetFolderId = '';
midas.pyslicer.statuslist.pdfSegmenterOutputFolderId = '';


$(document).ready(function(){
  
    $.post(json.global.webroot+'/pyslicer/user', {
        useAjax: true
        },
        function (results) {
            var resp = $.parseJSON(results);
            if(resp.status == 'ok' && resp.pyslicerUser) {
                midas.pyslicer.statuslist.pdfSegmenterRootFolderId = resp.pyslicerUser.root_folder_id;
                midas.pyslicer.statuslist.pdfSegmenterDataFolderId = resp.pyslicerUser.data_folder_id;
                midas.pyslicer.statuslist.pdfSegmenterPresetFolderId = resp.pyslicerUser.preset_folder_id;
                midas.pyslicer.statuslist.pdfSegmenterOutputFolderId = resp.pyslicerUser.output_folder_id;
            }
            else {
                midas.createNotice(resp.message, 3000, resp.status);
            }
        });

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

        var pdfSegmenterFolderIdsArg = midas.pyslicer.statuslist.pdfSegmenterRootFolderId ? '&pdfSegmenterRootFolderId=' + midas.pyslicer.statuslist.pdfSegmenterRootFolderId : '';
        pdfSegmenterFolderIdsArg += midas.pyslicer.statuslist.pdfSegmenterDataFolderId ? '&pdfSegmenterDataFolderId=' + midas.pyslicer.statuslist.pdfSegmenterDataFolderId : '';
        pdfSegmenterFolderIdsArg += midas.pyslicer.statuslist.pdfSegmenterPresetFolderId ? '&pdfSegmenterPresetFolderId=' + midas.pyslicer.statuslist.pdfSegmenterPresetFolderId : '';
        pdfSegmenterFolderIdsArg += midas.pyslicer.statuslist.pdfSegmenterOutputFolderId ? '&pdfSegmenterOutputFolderId=' + midas.pyslicer.statuslist.pdfSegmenterOutputFolderId : '';
        midas.pyslicer.statuslist.itemSelectionCallback = function(name, id) {
            var redirectUrl = $('.webroot').val() + '/pvw/paraview/slice?itemId=' + id + pdfSegmenterFolderIdsArg;
            redirectUrl += '&operations=paint&jsImports=' + $('.webroot').val() + '/modules/pyslicer/public/js/lib/pvw.pdfSegmenter.js;' + $('.webroot').val() + '/modules/pyslicer/public/js/simplecolorpicker.js';
            window.location = redirectUrl;
        };
    });

});

itemSelectionCallback = function(name, id)  {
  midas.pyslicer.statuslist.itemSelectionCallback(name, id);
  return;
}