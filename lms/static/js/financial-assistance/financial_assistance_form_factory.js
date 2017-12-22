    'use strict';

    define([
        'js/financial-assistance/views/financial_assistance_form_view'
    ],
    function(FinancialAssistanceFormView) {
        function FinancialAssistanceFactory(options) {
            var formView = new FinancialAssistanceFormView({
                el: '.financial-assistance-wrapper',
                context: options
            });

            return formView;
        };

        invokePageFactory(FinancialAssistanceFactory);
    });
