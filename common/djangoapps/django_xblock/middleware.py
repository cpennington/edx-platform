from django.conf import settings
import threading

_threadlocal = threading.local()
_threadlocal.runtimes = {}


class PerRequestRuntimeMiddleware(object):
    """
    Middleware to generate per-request XBlock runtimes upon request.
    """
    @classmethod
    def runtime(cls, key, **kwargs):
        """
        Create/retrieve the configured runtime for the current request.

        Args:
            key (str): The key to distinguish which runtime is to be retrieved
            **kwargs: Any additional keyword arguments will be used when constructing
                the runtime (which happens the first time it is requested with a particular
                key).
        """
        if key not in _threadlocal.runtimes:
            _threadlocal.runtimes[key] = settings.XBLOCK_RUNTIME(**kwargs)
        return _threadlocal.runtimes[key]

    def process_request(self, request):
        _threadlocal.runtimes.clear()

    def process_response(self, request, response):
        _threadlocal.runtimes.clear()
        return response
