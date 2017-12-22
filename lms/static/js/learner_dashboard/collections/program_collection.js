    'use strict';
    define([
        'backbone',
        'js/learner_dashboard/models/program_model'
    ],
    function(Backbone, Program) {
        return Backbone.Collection.extend({
            model: Program
        });
    });
