/**
 *  Store data to enroll learners into the course
 */
    'use strict';

    define([
        'backbone'
    ],
        function(Backbone) {
            return Backbone.Model.extend({
                defaults: {
                    course_id: '',
                    optIn: false
                }
            });
        }
    );
