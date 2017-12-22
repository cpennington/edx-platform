    define(['backbone'], function(Backbone) {
        'use strict';

        return Backbone.Model.extend({
            idAttribute: 'term',
            defaults: {
                facet: '',
                term: '',
                count: 0,
                selected: false
            }
        });
    });
