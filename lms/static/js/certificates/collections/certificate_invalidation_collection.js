// Backbone.js Application Collection: CertificateInvalidationCollection
/* global define, RequireJS */

    'use strict';

    define(
        ['backbone', 'js/certificates/models/certificate_invalidation'],

        function(Backbone, CertificateInvalidation) {
            return Backbone.Collection.extend({
                model: CertificateInvalidation,

                initialize: function(models, options) {
                    this.url = options.url;
                }
            });
        }
    );
