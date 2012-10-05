var midas = midas || {};
midas.visualize = midas.visualize || {};

midas.visualize.processPointMapHandler = function () {
    var points = {fixed: [], moving: []};
    $.each(midas.visualize.left.points, function(idx, point) {
        points.fixed.push([point.x, point.y, point.z]);
    });
    $.each(midas.visualize.left.points, function(idx, point) {
        points.moving.push([point.x, point.y, point.z]);
    });
    $('div.MainDialog').dialog('close');
    html= '<div><label>Output volume name</label><input style="width: 400px;" type="text" id="outputVolumeName" value="'
          +json.visualize.items.right.name+'_output_volume" />';
    html+= '<label>Output transform name</label><input style="width: 400px;" type="text" id="outputTransformName" value="'
          +json.visualize.items.right.name+'_output_transform" />';
    html+= '</div><br/><br/>';
    html+= '<img src="'+json.global.coreWebroot+'/public/images/icons/loading.gif" '
          +'id="processingPleaseWait" style="display: none;" />';
    html+= '<div style="float: right;">';
    html+= '<button class="globalButton processItemSlicerYes">Process</button>';
    html+= '<button style="margin-left: 15px;" class="globalButton processItemSlicerNo">Cancel</button>';
    html+= '</div>';
    midas.showDialogWithContent('Run landmark registration', html, false);
    $('#outputVolumeName').focus().select();

    $('button.processItemSlicerYes').unbind('click').click(function () {
        var args = 'fixed_item_id='+json.visualize.items.left.item_id;
        args += '&moving_item_id='+json.visualize.items.right.item_id;
        args += '&fixed_fiducials='+JSON.stringify(points.fixed);
        args += '&moving_fiducials='+JSON.stringify(points.moving);
        args += '&output_item_name='+$('#outputVolumeName').val();
        args += '&transform_type=Rigid';
        console.log(args);

        $('#processingPleaseWait').show();
        ajaxWebApi.ajax({
            method: 'midas.pyslicer.start.fiducialregistration',
            args: args,
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
