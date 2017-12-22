/**
 * A generic header model.
 */
    'use strict';
    define(['backbone'], function(Backbone) {
        var HeaderModel = Backbone.Model.extend({
            defaults: {
                'title': '',
                'description': '',
                'breadcrumbs': null,
                'nav_aria_label': ''
            }
        });

        return HeaderModel;
    });
