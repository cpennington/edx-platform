/**
 * Model for a topic.
 */
    'use strict';
    define(['backbone'], function(Backbone) {
        var Topic = Backbone.Model.extend({
            defaults: {
                name: '',
                description: '',
                team_count: 0,
                id: ''
            },

            initialize: function(options) {
                this.url = options.url;
            }
        });
        return Topic;
    });
