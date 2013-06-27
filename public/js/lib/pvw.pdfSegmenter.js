var midas = midas || {};
midas.pvw = midas.pvw || {};

/**
 * Activate paint mode as soon as we finished initialization
 */
midas.pvw.postInitCallback = function () {
    midas.pvw.paintMode();
    midas.pvw.pdfSegmenterPresets();
};

/**
 * Get the list of pdf segmenter preset json files
 */
midas.pvw.getPdfSegmenterPresets = function (id) {
    ajaxWebApi.ajax({
        method: 'midas.folder.children',
        args: 'id=' + id,
        success: function (results) {
            $("#selectedPresetFile").empty();
            $("#selectedPresetFile").append('<option value = "">default</option>');
            for (var key in results.data.items) {
                var item = results.data.items[key];
                if (/\.json$/.test(item.name)) { // only care about json files
                    var optionHtml = '<option value = "' + item.item_id + '">' + item.name.slice(0, -5) + '</option>';
                    $("#selectedPresetFile").append(optionHtml);
                }
            }
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            midas.createNotice(XMLHttpRequest.message, '4000', 'error');
        }
    });            
}

/*
 * Drop down list to select preset parameters (json file) for PDF segmenter
 */
midas.pvw.pdfSegmenterPresets = function () {
    midas.pvw.pdfSegmenterSelectedPresetItemId = '';
    midas.pvw.pdfSegmenterPresetFolderId = typeof(json.pvw.pdfSegmenterPresetFolderId) === 'undefined' ? '' : json.pvw.pdfSegmenterPresetFolderId;
    midas.pvw.pdfSegmenterOutputFolderId = typeof(json.pvw.pdfSegmenterOutputFolderId) === 'undefined' ? '' : json.pvw.pdfSegmenterOutputFolderId;

    var html = '<div class="sideElementActions viewAction">';
    html += '<h1 id="updatePdfPresets"><a id="pdfSegmenterPresetsFolder">Change PDF Segmenter Presets Folder</a></h1>';
    html += '<h1>PDF Segmenter Presets</h1>';
    html += '<select id="selectedPresetFile">';
    html += '<option value = "">default</option>';
    html += '</select>';
    html += '</div>';
    $(".viewSideBar").prepend(html);
    if (midas.pvw.pdfSegmenterPresetFolderId) {
        midas.pvw.getPdfSegmenterPresets(midas.pvw.pdfSegmenterPresetFolderId);
    }

    $("h1#updatePdfPresets").hover(
        function(){
            $("h1#updatePdfPresets").css("background-color","#E5E5E5");
        }, 
        function(){
            $("h1#updatePdfPresets").css("background-color","white");
        });

    $('a#pdfSegmenterPresetsFolder').click(function() {
        midas.loadDialog("selecfolder_pdfpresets","/browse/selectfolder?policy=read");
        midas.showDialog('Browse for the Folder Containng PDF Segmenter Preset JSON Files');
        midas.pvw.folderSelectionCallback = function(name, id) {
            midas.pvw.getPdfSegmenterPresets(id);
            midas.pvw.pdfSegmenterPresetFolderId = id;
        };
    });

    $('#selectedPresetFile').change(function(){
        midas.pvw.pdfSegmenterSelectedPresetItemId = $(this).val();
    })
}

/**
 * Callback handler to trigger PDF segmentation pipeline
 */
midas.pvw.handlePDFSegmentation = function (labelmapItemId, objectLabels) {
    $('div.MainDialog').dialog('close');
    // Get output item name
    var html = '<div><input style="width: 400px;" type="text" id="processItemSlicerOutputName" value="'
        + json.pvw.item.name + '_pdfseg_out" /></div><br/><br/>';
    html += '<img src="' + json.global.coreWebroot + '/public/images/icons/loading.gif" '
        + 'id="processingPleaseWait" style="display: none;" />';
    html += '<div style="float: right;">';
    html += '<button class="globalButton processItemSlicerYes">Process</button>';
    html += '<button style="margin-left: 15px;" class="globalButton processItemSlicerNo">Cancel</button>';
    html += '</div>';
    midas.showDialogWithContent('Choose name for output item', html, false);
    $('#processItemSlicerOutputName').focus();
    $('#processItemSlicerOutputName').select();

    $('button.processItemSlicerYes').unbind('click').click(function () {
        var outputItemName = $('#processItemSlicerOutputName').val();
        var outputLabelmap = $('#processItemSlicerOutputName').val() + '-label';

        $('#processingPleaseWait').show();
        var objectId = '['+objectLabels[0]+', '+objectLabels[1]+']'; // serialize objectId value
        var presetItemIdArg = midas.pvw.pdfSegmenterSelectedPresetItemId ? '&preset_item_id=' + midas.pvw.pdfSegmenterSelectedPresetItemId : '';
        var outputFolderIdArg = midas.pvw.pdfSegmenterOutputFolderId ? '&output_folder_id=' + midas.pvw.pdfSegmenterOutputFolderId : '';
        ajaxWebApi.ajax({
            method: 'midas.pyslicer.start.pdfsegmentation',
            args: 'item_id=' + json.pvw.item.item_id + '&labelmap_item_id=' + labelmapItemId + '&object_id=' + objectId + '&output_item_name=' + outputItemName + '&output_labelmap=' + outputLabelmap + presetItemIdArg + outputFolderIdArg,
            success: function (results) {
                $('div.MainDialog').dialog('close');
                $('#processingPleaseWait').hide();
                if (results.data.redirect) {
                    // Open job status url in another window so that users can continue painting
                    window.open(results.data.redirect, '_blank', 'resizable=yes,scrollbars=yes,toolbar=yes,menubar=no,location=yes,directories=no,status=yes');
                }
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                midas.createNotice(XMLHttpRequest.message, '4000', 'error');
                $('#processingPleaseWait').hide();
            }
        });
    });

    $('button.processItemSlicerNo').unbind('click').click(function () {
        $('div.MainDialog').dialog('close');
    });
}

folderSelectionCallback = function(name, id)  {
    midas.pvw.folderSelectionCallback(name, id);
    return;
}