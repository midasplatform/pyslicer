var midas = midas || {};
midas.pyslicer = midas.pyslicer || {};

// 30 second delay
midas.pyslicer.delayMillis = 30000;

$(document).ready(function()  {

    // start looping for updates
    var t = setTimeout(midas.pyslicer.updateJobCounts, midas.pyslicer.delayMillis);

});


midas.pyslicer.updateJobCounts = function() {
  ajaxWebApi.ajax(
    {
    method: 'midas.pyslicer.get.user.job.counts.by.status',  
    success: function(results) {
        $('#midas_pyslicer_jobcount_wait').html(results.data.wait);
        $('#midas_pyslicer_jobcount_started').html(results.data.started);
        $('#midas_pyslicer_jobcount_done').html(results.data.done);
        var t = setTimeout(midas.pyslicer.updateJobCounts, midas.pyslicer.delayMillis);
    },
    error: function() {
        console.log("Error getting user job counts by status");}
    });
}