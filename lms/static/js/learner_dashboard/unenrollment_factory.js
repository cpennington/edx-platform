    'use strict';

    define([
        'js/learner_dashboard/views/unenroll_view'
    ],
    function(UnenrollView) {
        function UnenrollmentFactory(options) {
            var Unenroll = new UnenrollView(options);
            return Unenroll;
        };

        invokePageFactory(UnenrollmentFactory);
    });
