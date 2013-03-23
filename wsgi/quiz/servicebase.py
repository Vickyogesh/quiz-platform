import hashlib
import time
import random

try:
    import simplejson as json
    print "Using simplejson to process JSON"
except ImportError:
    import json
    print "Using json to process JSON"

import traceback
from werkzeug.utils import cached_property
from werkzeug.exceptions import HTTPException, Unauthorized, BadRequest
from werkzeug.routing import Map, Rule, BaseConverter
from werkzeug.wrappers import Request, Response
from quiz.core.core import QuizCore
from quiz.core.exceptions import QuizCoreError


class QuizWWWAuthenticate(object):
    """"Provides simple WWW-Authenticate header for the Quiz service."""
    def __init__(self):
        self.random = random.random()
        self.time = time.time()

    def to_header(self):
        """Convert the stored values into a WWW-Authenticate header."""
        m = hashlib.md5()
        m.update('{0}:{1}'.format(self.random, self.time))
        return 'QuizAuth nonce="%s"' % m.hexdigest()

    def to_dict(self):
        m = hashlib.md5()
        m.update('{0}:{1}'.format(self.random, self.time))
        return {'nonce': m.hexdigest()}


class IdConverter(BaseConverter):
    """Converter to use in Rules.

    Provides int or 'me' identifiers.
    """
    def __init__(self, url_map):
        super(IdConverter, self).__init__(url_map)
        self.regex = '(?:me|\d+)'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


class JSONRequest(Request):
    """JSON Requests.

    Converts response data to the JSON object.
    You may acces to the data via request.json.
    """
    # accept up to 4MB of transmitted data.
    max_content_length = 1024 * 1024 * 4

    @cached_property
    def json(self):
        cnt = self.headers.get('content-type')
        if cnt and 'application/json' in cnt:
            try:
                data = json.loads(self.data)
            except Exception:
                raise BadRequest('Not a JSON.')
            else:
                return data
        else:
            raise BadRequest('Not a JSON.')


class JSONResponse(Response):
    """Provides JSON response.

    It converts response param to the JSON string and set
    contetn type to application/json, also 'status' filed will be added.
    """
    default_json = '{"status":200}'
    json_separators = (',', ':')

    def __init__(self, response=None, status=None, headers=None,
                 mimetype=None, direct_passthrough=False):
        if response is None:
            response = self.default_json
        elif isinstance(response, dict):
            if 'status' not in response:
                response['status'] = status or 200
            response = json.dumps(response, separators=self.json_separators)
        super(JSONResponse, self).__init__(
            response, 200, headers=headers, mimetype=mimetype,
            content_type='application/json; charset=utf-8',
            direct_passthrough=direct_passthrough)


class ServiceBase(object):
    """Base class for web service.

    Features: URL routing, HTTP errors processing,
    authorization and session validation.
    Subclass needs to fill self.urls map.
    """
    def __init__(self, settings):
        random.seed()
        self.settings = settings
        self.urls = Map([Rule('/authorize', endpoint='on_authorize')],
                        converters={'uid': IdConverter})
        self.core = QuizCore(settings)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def __assert_session(self):
        if "user_id" not in self.session:
            raise Unauthorized

    # Dispatch request and validate seassion if needed
    def __dispatch(self, request):
        self.session = request.environ['beaker.session']
        adapter = self.urls.bind_to_environ(request.environ)

        try:
            endpoint, values = adapter.match()
            if endpoint != 'on_authorize':
                self.__assert_session()
            return getattr(self, endpoint)(request, **values)
        except HTTPException, e:
            return e

    def __handleErrorsAsJSON(self, request):
        try:
            response = self.__dispatch(request)
            if isinstance(response, HTTPException):
                raise response
        except HTTPException as e:
            if e.code == 404:   # don't wrap 404 error
                return e
            res = e.get_response(request.environ)
            response = JSONResponse({
                'status': e.code,
                'description': res.data,
            }, headers=res.headers)
        except QuizCoreError as e:
            response = JSONResponse({
                'status': 400,
                'description': e.message
            })
        except Exception as e:
            traceback.print_exc()
            response = JSONResponse({
                'status': 500,
                'description': 'INTERNAL SERVER ERROR'
            })
        return response

    def wsgi_app(self, environ, start_response):
        request = JSONRequest(environ)
        response = self.__handleErrorsAsJSON(request)
        try:
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
        except:
            pass
        return response(environ, start_response)

    def __check_digest(self, nonce, digest, passwd):
        m = hashlib.md5()
        m.update('%s:%s' % (nonce, passwd))
        mx = m.hexdigest()
        return mx == digest

    def __onValidateAuth(self, request, data):
        try:
            nonce = data["nonce"]
            login = data["login"]
            appid = data["appid"]
            digest = data["digest"]
        except KeyError:
            raise BadRequest('Invalid parameters.')

        data = self.core.getUserAndAppInfo(login, appid)

        if not data or not self.__check_digest(nonce, digest, data['passwd']):
            raise BadRequest('Authorization is invalid.')

        self.session['app_id'] = data['app_id']
        self.session['user_id'] = data['user_id']
        self.session['user_name'] = data['name']
        self.session['user_surname'] = data['surname']
        self.session['user_type'] = data['type']
        self.session.save()

        # NOTE: we you want to use 'beaker.session.secret' then use:
        # sid = self.session.__dict__['_headers']['cookie_out']
        # sid = sid[sid.find('=') + 1:sid.find(';')]
        sid = self.session.id

        user = {
            'id': data['user_id'],
            'name': data['name'],
            'surname': data['surname'],
            'type': data['type']
        }

        if user['surname'] is None:
            del user['surname']

        return JSONResponse({'sid': sid, 'user': user})

    def on_authorize(self, request):
        try:
            data = request.json
        except BadRequest:
            return JSONResponse(QuizWWWAuthenticate().to_dict(), status=401)
        else:
            return self.__onValidateAuth(request, data)
