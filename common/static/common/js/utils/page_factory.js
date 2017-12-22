define([], function () {
    return function invokePageFactory(factory) {
        if (typeof window.pageFactoryArguments == "undefined") {
            throw "window.pageFactoryArguments must be initialized before calling invokePageFactory. Use the <%static:require_page> template tag.";
        }
        args = window.pageFactoryArguments[factory.name];

        if (typeof args == "undefined") {
            throw "window.pageFactoryArguments[\"" + factory.name + "\"] must be initialized before calling invokePageFactory. Use the <%static:require_page> template tag."
        }
        factory(...window.pageFactoryArguments[factory.name]);
    };
});
