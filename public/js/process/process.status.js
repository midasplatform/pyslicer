var midas = midas || {};
midas.pyslicer = midas.pyslicer || {};
midas.pyslicer.process = midas.pyslicer.process || {};

midas.pyslicer.process.delayMillis = 3000;


$(document).ready(function(){
    midas.pyslicer.process.refreshView(json.jobStatusesCount, json.jobStatus);
});


midas.pyslicer.process.isCompleted = function(jobStatus) {
    // complete is 2, error is 3
    return (jobStatus < 2);  
}

midas.pyslicer.process.refreshView = function(jobStatusesCount, jobStatus) {
    // display the table if there are rows to show
    if(jobStatusesCount > 0) {
        $('#midas_pyslicer_jobstatuses').show();      
        $('#midas_pyslicer_jobstatuses_loading').hide();
    }
    else {
        $('#midas_pyslicer_jobstatuses').hide();
        // show the loading icon if we are not yet complete or in error
        if(midas.pyslicer.process.isCompleted(jobStatus)) {
            $('#midas_pyslicer_jobstatuses_loading').show();
        }
    }
    // update the job status if we are not yet complete or in error
    if(midas.pyslicer.process.isCompleted(jobStatus)) {
        var t = setTimeout(midas.pyslicer.process.updateJobStatus, midas.pyslicer.process.delayMillis);
    }
}


midas.pyslicer.process.updateJobStatus = function() {
    var jobId = json.jobId;
    var args =  'job_id=' + jobId;

    ajaxWebApi.ajax({
        method: 'midas.pyslicer.get.jobstatus',
        args: args,
        success: function(results) {
            // update the status of the job
            $('#midas_pyslicer_job_status').empty();
            var statusString = json.statusStrings[results.data.job.status];
            var statusClass = json.statusClasses[results.data.job.status];
            $('#midas_pyslicer_job_status').addClass(statusClass);
            $('#midas_pyslicer_job_status').html(statusString);
                
            // hide the table and show loading icon during update
            $('#midas_pyslicer_jobstatuses').hide();
            $('#midas_pyslicer_jobstatuses_loading').show();
            
            // remove existing rows
            $('#midas_pyslicer_jobstatuses .statusRow').remove();

            var columns = ['event_type', 'message', 'notify_date'];
            $.each(results.data.jobstatuses, function(index, statusrow) {
                var html = '';
                html+='<tr class="statusRow">';
                var emptyNotifyDateColVal = '';
                if(midas.pyslicer.process.isCompleted(results.data.job.status)) {
                    emptyNotifyDateColVal = '<img alt="Loading..." src="'+json.global.coreWebroot+'/public/images/icons/loading.gif" />';    
                }
                $.each(columns, function (col_index, column)  {
                    var colval = statusrow[column];
                    if(colval == null) {
                        if(column == 'notify_date') {
                            colval = emptyNotifyDateColVal;    
                        }
                        else {
                            colval = "";
                        }
                    }
                    html+=' <td>'+colval+'</td>';
                });
                html+='</tr>';
                $('#midas_pyslicer_jobstatuses').append(html);
            });
            
            if(results.data.output_links.length > 0) {
                $('.outputLink').remove();
                $.each(results.data.output_links, function(index, outputLink) {
                    var link = '<a class="outputLink" href="'+outputLink.url+'">';
                    link += outputLink.text+'</a>';  
                    $('.viewOutput').append(link);
                });
            }
            
            if(results.data.condition_rows.length > 0) {
                $('#midas_pyslicer_error_div').remove();
                var error_div = '<div id="midas_pyslicer_error_div"><span class="midas_pyslicer_error">Error Trace:</span>';
                error_div += '<ul id="midas_pyslicer_jobstatus_condition">';
                $.each(results.data.condition_rows, function(index, conditionRow) {
                    error_div +=  '<li>'+conditionRow+'</li>';
                });
                error_div += '</ul></div>';
                $('#midas_pyslicer_jobstatus_header').append(error_div);                
            }
            
            midas.pyslicer.process.refreshView(results.data.jobstatuses.length, results.data.job.status);
        },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                midas.createNotice(XMLHttpRequest.message, '4000', 'error');
            }
        });
    
};
