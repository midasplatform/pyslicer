var midas = midas || {};
midas.pyslicer = midas.pyslicer || {};

midas.pyslicer.validateConfig = function (formData, jqForm, options) {
}

midas.pyslicer.successConfig = function (responseText, statusText, xhr, form) {
  try {
      var jsonResponse = jQuery.parseJSON(responseText);
  } catch (e) {
      midas.createNotice("An error occured. Please check the logs.", 4000, 'error');
      return false;
  }
  if(jsonResponse == null) {
      midas.createNotice('Error', 4000, 'error');
      return;
  }
  midas.createNotice(jsonResponse.message, 4000, jsonResponse.status);
}

$(document).ready(function() {
    $('#slicerProxyUrl').qtip({
        content: 'URL of the twisted server that acts as a proxy for the Slicer instance'
    });

    $('form.pyslicerConfigForm').ajaxForm({
        beforeSubmit: midas.pyslicer.validateConfig,
        success: midas.pyslicer.successConfig
    });
});
