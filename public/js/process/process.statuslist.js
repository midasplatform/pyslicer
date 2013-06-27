var midas = midas || {};
midas.pyslicer = midas.pyslicer || {};
midas.pyslicer.statuslist = midas.pyslicer.statuslist || {};

midas.pyslicer.statuslist.pdfSegmenterRootFolderId = '';
midas.pyslicer.statuslist.pdfSegmenterDataFolderId = '';
midas.pyslicer.statuslist.pdfSegmenterPresetFolderId = '';
midas.pyslicer.statuslist.pdfSegmenterOutputFolderId = '';


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
    
    $('a#createPdfSegmenterFolders').click(function() {
        midas.loadDialog("selecfolder_pdfpresets","/browse/selectfolder?policy=read");
        midas.showDialog('Browse for PDF Segmentation Root Folder');
        midas.pyslicer.statuslist.folderSelectionCallback = function(name, id) {
            midas.pyslicer.statuslist.pdfSegmenterRootId = id;
            ajaxWebApi.ajax({
                method: 'midas.pyslicer.create.pdfsegmentation.folders',
                args: 'root_folder_id=' + id,
                success: function (results) {
                    midas.pyslicer.statuslist.pdfSegmenterDataFolderId = results.data.dataFolderId;
                    midas.pyslicer.statuslist.pdfSegmenterPresetFolderId = results.data.presetFolderId;
                    midas.pyslicer.statuslist.pdfSegmenterOutputFolderId = results.data.outputFolderId;
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    midas.createNotice(XMLHttpRequest.message, '4000', 'error');
                }
            });
        };
    });
});

itemSelectionCallback = function(name, id)  {
  midas.pyslicer.statuslist.itemSelectionCallback(name, id);
  return;
}

folderSelectionCallback = function(name, id)  {
    midas.pyslicer.statuslist.folderSelectionCallback(name, id);
    return;
}