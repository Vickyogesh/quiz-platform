import random
from werkzeug.exceptions import HTTPException, Unauthorized
from werkzeug.routing import Map, Rule, BaseConverter
from werkzeug.wrappers import Request
from quiz.core import QuizCore
from quiz.serviceauth import AuthMixin


class IdConverter(BaseConverter):
    def __init__(self, url_map):
        super(IdConverter, self).__init__(url_map)
        self.regex = '(?:me|\d+)'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


class ServiceBase(AuthMixin):
    """
    Base class for web service.

    Features: URL routing, HTTP errors processing,
    authorization and session validation.
    Subclass must fill self.urls and
    implement endpoint methods as on_<endpoint_name>(...)
    """

    def __init__(self, settings):
        random.seed()
        self.settings = settings
        self.core = QuizCore(settings)
        self.urls = Map([Rule('/authorize', endpoint='on_authorize')],
                        converters={'uid': IdConverter})

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def _assert_session(self):
        if "user_id" not in self.session:
            raise Unauthorized

    # Dispatch request and validate seassion if needed
    def _dispatch(self, request):
        self.session = request.environ['beaker.session']
        adapter = self.urls.bind_to_environ(request.environ)

        try:
            endpoint, values = adapter.match()
            if endpoint != 'on_authorize':
                self._assert_session()
            return getattr(self, endpoint)(request, **values)
        except HTTPException, e:
            return e

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self._dispatch(request)
        return response(environ, start_response)
