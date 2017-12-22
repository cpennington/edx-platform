    'use strict';

    define(['js/api_admin/views/catalog_preview'], function(CatalogPreviewView) {
        function CatalogPreviewFactory(options) {
            var view = new CatalogPreviewView({
                el: '.catalog-body',
                previewUrl: options.previewUrl,
                catalogApiUrl: options.catalogApiUrl
            });
            return view.render();
        };

        invokePageFactory(CatalogPreviewFactory);
    });
