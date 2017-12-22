/**
 *  Store data for the current
 */
    'use strict';

    define([
        'backbone'
    ],
        function(Backbone) {
            return Backbone.Model.extend({
                defaults: {
                    availableSessions: [],
                    entitlementUUID: '',
                    currentSessionId: '',
                    userId: '',
                    courseName: ''
                }
            });
        }
    );
