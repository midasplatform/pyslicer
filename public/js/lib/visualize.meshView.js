var midas = midas || {};
midas.visualize = midas.visualize || {};

/**
 * Put the output mesh of the segmented region into the correct orientation to align
 * with the input volume, and change its color to red.
 */
midas.visualize.postInitCallback = function () {
    $.each(midas.visualize.meshes, function(k, mesh) {
        paraview.SetDisplayProperties({
            proxy: mesh.source,
            DiffuseColor: [1.0, 0.0, 0.0],
            Orientation: [180.0, 180.0, 0.0] 
        });
    });
};

