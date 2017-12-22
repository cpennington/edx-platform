window.Poll = function(el) {
    require(['PollMain'], function(PollMain) {
        new PollMain(el);
    });
};
