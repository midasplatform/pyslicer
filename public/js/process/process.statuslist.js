$(window).load(function () {
    $('a.paramsLink').click(function () {
        midas.showDialogWithContent('Job Parameters', $(this).attr('qtip'), false);
    });
});
