$(document).ready(function() {

  $('a#pyslicerProcessItem').click(function () {
      html= '<input type="text" id="processItemSlicerOutputName" value="output from slicer"/>';
      html+= '<div style="float: right;">';
      html+= '<input class="globalButton processItemSlicerYes" type="button" value="Process"/>';
      html+= '<input style="margin-left:15px;" class="globalButton processItemSlicerNo" type="button" value="Cancel"/>';
      html+= '</div>';
      midas.showDialogWithContent('Set output item name', html, false);

        $('input.processItemSlicerYes').unbind('click').click(function () {
            var outputItemName = $('#processItemSlicerOutputName').val();
            
            // TODO need to get seed value (x,y,z)
            var seed = '0,0,0';
            
            ajaxWebApi.ajax({
                method: 'midas.pyslicer.start.item.processing',  
                args: 'item_id=' + json.item.item_id + '&output_item_name=' + outputItemName + '&seed=' + seed,
                success: function(results) {
                    $( "div.MainDialog" ).dialog('close');
                },
                error: function(XMLHttpRequest, textStatus, errorThrown) {
                    midas.createNotice(XMLHttpRequest.message, "4000", 'error');
                }
            })
            
        });

        $('input.processItemSlicerNo').unbind('click').click(function() {
            $( "div.MainDialog" ).dialog('close');
        });

    });
});