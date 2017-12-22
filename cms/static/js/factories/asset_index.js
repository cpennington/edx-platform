define([
    'jquery', 'js/collections/asset', 'js/views/assets', 'jquery.fileupload', 'common/js/utils/page_factory'
], function($, AssetCollection, AssetsView, invokePageFactory) {
    'use strict';
    function AssetIndexFactory(config) {
        var assets = new AssetCollection(),
            assetsView;

        assets.url = config.assetCallbackUrl;
        assetsView = new AssetsView({
            collection: assets,
            el: $('.wrapper-assets'),
            uploadChunkSizeInMBs: config.uploadChunkSizeInMBs,
            maxFileSizeInMBs: config.maxFileSizeInMBs,
            maxFileSizeRedirectUrl: config.maxFileSizeRedirectUrl
        });
        assetsView.render();
    };

    invokePageFactory(AssetIndexFactory);
});
