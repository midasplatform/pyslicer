var midas = midas || {};
midas.pyslicer = midas.pyslicer || {};
midas.pyslicer.process = midas.pyslicer.process || {};

midas.pyslicer.process.delayMillis = 10000;


$(document).ready(function(){
   
    var t = setTimeout(midas.pyslicer.process.updateJobStatus, midas.pyslicer.process.delayMillis);
    
});

midas.pyslicer.process.updateJobStatus = function() {
       var jobId = json.jobId;;
       var args =  'job_id=' + jobId;

       ajaxWebApi.ajax({
            method: 'midas.pyslicer.get.jobstatus',
            args: args,
            success: function(results) {
                console.log(results);
                // also need to update actual table rows

                  //  $this->view->json['jobId'] = $jobId;
    //$this->view->json['statusStrings'] = $this->statusStrings;
    //$this->view->json['statusClasses']

                $('#midas_pyslicer_job_status').empty();
                var statusString = json.statusStrings[results.data.job.status];
                var statusClass = json.statusClasses[results.data.job.status];
                $('#midas_pyslicer_job_status').addClass(statusClass);
                $('#midas_pyslicer_job_status').html(statusString);

//                var status
                
                $('#midas_pyslicer_jobstatuses').hide();
                // remove existing rows
                $('#midas_pyslicer_jobstatuses .statusRow').remove();

                // TODO also update job status, condition
                var columns = ['event_type', 'message', 'notify_date'];
                $.each(results.data.jobstatuses, function(index, statusrow) {
                    var html = '';
                    console.log(statusrow);
                    html+='<tr class="statusRow">';
                    $.each(columns, function (col_index, column)  {
                        var colval = statusrow[column];
                        if(colval == null) {
                            colval = "";
                        }
                        html+=' <td>'+colval+'</td>';
                    });
                    html+='</tr>';
                    // sort these by event_id, also some duplication
                    $('#midas_pyslicer_jobstatuses').append(html);
                    
                    
                    
                    
                });

                $('#midas_pyslicer_jobstatuses').show();
                
                // some notion of whether to loop again
                // probably if job is not done or not in error
                var t = setTimeout(midas.pyslicer.process.updateJobStatus, midas.pyslicer.process.delayMillis);
                
 
            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                midas.createNotice(XMLHttpRequest.message, '4000', 'error');
            }
        });
    
};
