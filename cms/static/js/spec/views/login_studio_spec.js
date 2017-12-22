define(['require', 'jquery', 'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
        'common/js/components/utils/view_utils'],
function(require, $, AjaxHelpers, ViewUtils) {
    'use strict';
    describe('Studio Login Page', function() {
        var submitButton;

        beforeEach(function() {
            loadFixtures('mock/login.underscore');
            window.pageFactoryArguments.LoginFactory = ['/home/'];
            require(['js/factories/login']);
            submitButton = $('#submit');
        });

        it('disable the submit button once it is clicked', function() {
            spyOn(ViewUtils, 'redirect').and.callFake(function() {});
            var requests = AjaxHelpers.requests(this);
            expect(submitButton).not.toHaveClass('is-disabled');
            submitButton.click();
            AjaxHelpers.respondWithJson(requests, {'success': true});
            expect(submitButton).toHaveClass('is-disabled');
        });

        it('It will not disable the submit button if there are errors in ajax request', function() {
            var requests = AjaxHelpers.requests(this);
            expect(submitButton).not.toHaveClass('is-disabled');
            submitButton.click();
            expect(submitButton).toHaveClass('is-disabled');
            AjaxHelpers.respondWithError(requests, {});
            expect(submitButton).not.toHaveClass('is-disabled');
        });
    });
});
