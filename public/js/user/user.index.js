var midas = midas || {};
midas.pyslicer = midas.pyslicer || {};
midas.pyslicer.user = midas.pyslicer.user || {};

midas.pyslicer.user.createPdfSegmenterFolders = function() {
    midas.loadDialog("selectitem_volumeRendering","/browse/selectfolder?policy=read");
    midas.showDialog('Browse for PDF Segmentation Root Folder');
    midas.pyslicer.user.folderSelectionCallback = function(name, id) {
        $.post(json.global.webroot+'/pyslicer/user/createfolders', {
            rootFolderId: id
        },
        function (text) {
            var resp = $.parseJSON(text);
            if(resp.status == 'ok' && resp.pyslicerUser) {
                midas.createNotice(resp.message, 3000, resp.status);
                midas.pyslicer.user.addPyslicerUserToList(resp.pyslicerUser)
            }
            else {
                midas.createNotice(resp.message, 3000, resp.status);
            }
        });
    };
};

midas.pyslicer.user.addPyslicerUserToList = function (pyslicerUser) {
    $('.pyslicerUserTable tbody').empty();
    var html = '<tr><td><a href='+json.global.webroot+'/folder/'+
        pyslicerUser.root_folder_id+'>'+ pyslicerUser.root_folder_id+'</a>'+
        '</td><td><a href='+json.global.webroot+'/folder/'+
        pyslicerUser.data_folder_id+'>'+pyslicerUser.data_folder_id+'</a>'+
        '</td><td><a href='+json.global.webroot+'/folder/'+
        pyslicerUser.preset_folder_id+'>'+ pyslicerUser.preset_folder_id+'</a>'+
        '</td><td><a href='+json.global.webroot+'/folder/'+
        pyslicerUser.output_folder_id+'>'+pyslicerUser.output_folder_id+'</a>'+
        '</td><td><a class="deletePyslicerUserLink">Unset</a></td></tr>';
    $('.pyslicerUserTable tbody').append(html);
    $('a.deletePyslicerUserLink').unbind('click').click(midas.pyslicer.user.confirmDeletePyslicerUser);
    $('.noFoldersMessage').hide();
};

midas.pyslicer.user.confirmDeletePyslicerUser = function() {
    var parentRow = $(this).parents('tr');
    midas.showDialogWithContent('Unset default folder for PDF segmenter', $('#template-deletePyslicerUserDialog').html());
    var container = $('div.MainDialog');
    container.find('.deletePyslicerUserYes').click(function () {
        $.post(json.global.webroot+'/pyslicer/user/delete',
            function (text) {
                var resp = $.parseJSON(text);
                $('div.MainDialog').dialog('close');
                if(resp.status == 'ok') {
                    midas.createNotice(resp.message, 3000, resp.status);
                    $(parentRow).remove();
                    $('.noFoldersMessage').show();
                }
                else {
                    midas.createNotice(resp.message, 3000, resp.status);
                }
            }
        );
    });
    container.find('.deletePyslicerUserNo').click(function () {
        $('div.MainDialog').dialog('close');
    });
};

$(document).ready(function(){
    $('a.createPdfSegmenterFolders').click(midas.pyslicer.user.createPdfSegmenterFolders);
    $('a.deletePyslicerUserLink').click(midas.pyslicer.user.confirmDeletePyslicerUser);
    $("a.createPdfSegmenterFolders").hover(
        function(){
            $("a.createPdfSegmenterFolders").css("background-color","#E5E5E5");
        },
        function(){
            $("a.createPdfSegmenterFolders").css("background-color","white");
        });

});

folderSelectionCallback = function(name, id)  {
    midas.pyslicer.user.folderSelectionCallback(name, id);
    return;
}