var midas = midas || {};
midas.pyslicer = midas.pyslicer || {};
midas.pyslicer.console = midas.pyslicer.console || {};


midas.pyslicer.console.prompt = ">>>";


midas.pyslicer.console.ready = function() {
    midas.pyslicer.console.display.text(midas.pyslicer.console.prompt);    
    
}



$(document).ready(function(){
    midas.pyslicer.console.display = $('#pyslicer_console');
    midas.pyslicer.console.ready();
});