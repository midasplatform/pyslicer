var midas = midas || {};
midas.pvw = midas.pvw || {};

/**
 * Activate paint mode as soon as we finished initialization
 */
midas.pvw.postInitCallback = function () {
    $('button.paintButton').click();
};

/**
 * Callback handler to trigger pdf segmentation pipeline
 */
midas.pvw.handlePDFSegmentation = function (labelmapItemId) {
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
        ajaxWebApi.ajax({
            method: 'midas.pyslicer.start.pdfsegmentation',
            args: 'item_id=' + json.pvw.item.item_id + '&labelmap_item_id=' + labelmapItemId + '&output_item_name=' + outputItemName + '&output_labelmap=' + outputLabelmap,
            success: function (results) {
                $('div.MainDialog').dialog('close');
                $('#processingPleaseWait').hide();
                if (results.data.redirect) {
                    // Open job status url in another window so that users can continue paiting
                    window.open(results.data.redirect);
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
};
