var midas = midas || {};
midas.visualize = midas.visualize || {};

/**
 * Activate point selection mode as soon as we are done initializing
 */
midas.visualize.postInitCallback = function () {
    $('button.pointSelectButton').click();
};

/**
 * Callback handler for point selection within an image
 */
midas.visualize.handlePointSelect = function (point) {
    $('div.MainDialog').dialog('close');
    html= '<div><input style="width: 400px;" type="text" id="processItemSlicerOutputName" value="'
          +json.visualize.item.name+'_seg_out" /></div><br/><br/>';
    html+= '<img src="'+json.global.coreWebroot+'/public/images/icons/loading.gif" '
          +'id="processingPleaseWait" style="display: none;" />';
    html+= '<div style="float: right;">';
    html+= '<button class="globalButton processItemSlicerYes">Process</button>';
    html+= '<button style="margin-left: 15px;" class="globalButton processItemSlicerNo">Cancel</button>';
    html+= '</div>';
    midas.showDialogWithContent('Choose name for output item', html, false);
    $('#processItemSlicerOutputName').focus();
    $('#processItemSlicerOutputName').select();

    $('button.processItemSlicerYes').unbind('click').click(function () {
        var outputItemName = $('#processItemSlicerOutputName').val();
        var seed = '['+point[0]+', '+point[1]+', '+point[2]+']'; // serialize seed point value

        $('#processingPleaseWait').show();
        ajaxWebApi.ajax({
            method: 'midas.pyslicer.start.item.processing',
            args: 'item_id='+json.visualize.item.item_id+'&output_item_name='+outputItemName+'&seed='+seed,
            success: function(results) {
                $('div.MainDialog').dialog('close');
                $('#processingPleaseWait').hide();
                if(results.data.redirect) {
                    window.location = results.data.redirect;
                }
            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                midas.createNotice(XMLHttpRequest.message, '4000', 'error');
                $('#processingPleaseWait').hide();
            }
        });
        
    });

    $('button.processItemSlicerNo').unbind('click').click(function () {
        $('div.MainDialog').dialog('close');
    });
};

