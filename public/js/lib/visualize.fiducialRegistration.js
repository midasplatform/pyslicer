var midas = midas || {};
midas.visualize = midas.visualize || {};

midas.visualize.processPointMapHandler = function () {
    midas.createNotice('success', 1500, 'ok');
    console.log(midas.visualize.left.points);
    console.log(midas.visualize.right.points);
    console.log('left item id = '+json.visualize.items.left.item_id);
    console.log('right item id = '+json.visualize.items.right.item_id);
};
