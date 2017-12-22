    'use strict';
    define('js/student_account/views/finish_auth_factory',
        ['jquery', 'underscore', 'backbone', 'js/student_account/views/FinishAuthView', 'utility'],
        function($, _, Backbone, FinishAuthView) {
            return function() {
                var view = new FinishAuthView({});
                view.render();
            };
        }
    );
