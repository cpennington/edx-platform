    'use strict';
    define(['jquery', 'teams/js/views/teams_tab'],
        function($, TeamsTabView) {
            function TeamsTabFactory(options) {
                var teamsTab = new TeamsTabView({
                    el: $('.teams-content'),
                    context: options,
                    viewLabel: gettext('Teams')
                });
                teamsTab.start();
            };

            invokePageFactory(TeamsTabFactory);
        });
