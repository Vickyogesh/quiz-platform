try:
    import simplejson as json
    print "Using simplejson to process JSON"
except ImportError:
    import json
    print "Using json to process JSON"

import os.path
import random
import traceback
import hashlib
import time

from werkzeug.utils import cached_property
from werkzeug.exceptions import HTTPException, BadRequest, Unauthorized, Forbidden
from werkzeug.routing import Map, Rule, BaseConverter
from werkzeug.wrappers import Request, Response
from beaker.middleware import SessionMiddleware

from .middleware import QuizMiddleware
from .settings import Settings
from .core.core import QuizCore
from .core.exceptions import QuizCoreError


def _check_digest(nonce, digest, passwd):
    m = hashlib.md5()
    m.update('%s:%s' % (nonce, passwd))
    mx = m.hexdigest()
    return mx == digest


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


class QuizApp(object):
    """Quiz WSGI application.

    Provides the following features:

        * JSON responses.
        * Convert exceptions and HTTP errors to JSON.
        * Session management and CORS requests (See QuizApp.wrap()).
        * Authorization.
        * Requests access privileges.
        * 'guest' access control.
    """
    def __init__(self):
        self.settings = self.__getSettings()
        self.core = QuizCore(self.settings)
        self.urls = Map(converters={'uid': IdConverter})
        self.endpoints = {}

        # Default handlers for authorization.
        self.addRule('/authorize', self.onNewAuth, methods=['GET'])
        self.addRule('/authorize', self.onDoAuth, methods=['POST'])

    # Read application settings.
    # There may be two sources:
    #   1. $OPENSHIFT_DATA_DIR/quiz/congig.ini
    #   2. [src]/test-data/config.ini
    # At first (1) will be loaded, if this file is not exsist
    # then (2) will be loaded. (2) is used for development only
    # and (1) must be used for production.
    def __getSettings(self):
        # Construct data path using OpenShift env
        oshift_path = os.getenv('OPENSHIFT_DATA_DIR', '')
        oshift_path = os.path.join(oshift_path, 'quiz')
        oshift_path = os.path.normpath(oshift_path)

        # Construct additional data path for testing purpose.
        # It will be used while development on local host.
        path = os.path.dirname(__file__)
        path = os.path.join(path, '..', '..', 'test-data')
        path = os.path.normpath(path)

        return Settings([oshift_path, path])

    def __call__(self, environ, start_response):
        self.request = JSONRequest(environ)
        response = self.__handleErrorsAsJSON(self.request)
        self.request = None  # TODO: do we really need this?

        # Add extra headers for the CORS support.
        # See middleware.py for more info.
        try:
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
        except:
            pass
        return response(environ, start_response)

    # Catch runtime errors and convert them to JSON.
    # Return JSONResponse.
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
                'description': e.get_description(request.environ),
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

    # Dispatch request.
    # Request will be dispatched only if session user has
    # access to it. See __can_access() comments.
    def __dispatch(self, request):
        self.session = request.environ['beaker.session']
        adapter = self.urls.bind_to_environ(request.environ)
        endpoint, args = adapter.match()
        access, handler = self.endpoints[endpoint]

        if self.__can_access(access):
            return self.__call_handler(access, handler, args)
        else:
            raise Forbidden('Forbidden.')

    # Check access to the API + session validation.
    # How access is implemented:
    # User type is stored in the 'user_type' inside session.
    # This value must be set while authorization and it will be
    # checked if user is authorized.
    # Access privs for API are set via rule(), get() and post() decorators.
    #
    # If access is None then we assume what API is avaliable to anyone,
    # even non-authorized users.
    # If user type is present in the access property of the API call
    # then the call will be allowed.
    # If access contains '*' then API call is allowed to any authorized user.
    def __can_access(self, access):
        if access is None:
            return True
        try:
            user_type = self.session['user_type']
        except Exception:
            raise Unauthorized('Unauthorized.')
        can = '*' in access or user_type in access
        return can

    # Store last visit timestamp for all users (except admin)
    # and also validate guest access if needed before calling
    # request handler.
    def __call_handler(self, access, handler, args):
        # If access privs are not set then we skip
        # guest access and last visit time saving.
        if access:
            utype = self.session['user_type']
            uid = self.session['user_id']
            if utype == 'guest':
                if not self.core.processGuestAccess(uid):
                    raise Forbidden('Forbidden.')
            if utype == 'student' or utype == 'guest':
                self.core.updateUserLastVisit(uid)

        return handler(**args)

    def addRule(self, rule, func, endpoint=None, **opts):
        """Add routing rule.

        If :param endpoint: is None then :param func: name will be used
        as endpoint.
        :param opts: can contains any parameters for werkzeug's Rule.
        Additionally **access** parameter is used to configure
        access privs for the request.
        """
        access = opts.pop('access', None)

        if access is not None and not isinstance(access, list):
            ValueError('access value can be a list or None.')

        if endpoint is None:
            endpoint = func.__name__

        opts['endpoint'] = endpoint

        # If endpoint alread exists we make sure what
        # the same handler and access privs are used.
        if endpoint in self.endpoints:
            a, h = self.endpoints[endpoint]
            if a != access or h != func:
                raise AssertionError('Already mapped: %s' % endpoint)

        self.urls.add(Rule(rule, **opts))
        self.endpoints[endpoint] = (access, func)

    def route(self, rule, **opts):
        """A decorator that is used to register request handler.

        Examples:

            @app.route('/some_url/<int:id>', methods=['GET', 'POST'])
            def handler(id): ...

            @app.route('/some_url/<int:id>', access=['admin'], methods=['GET'])
            def handler(id): ...
        """
        def decorator(f):
            self.addRule(rule, f, **opts)
            return f
        return decorator

    def post(self, rule, access=None):
        """A decorator that is used to register POST request handler.

        Example:
            @app.post('/some_url/<int:id>', access=['*'])
            def handler(id): ...
        """
        return self.route(rule, access=access, methods=['POST'])

    def get(self, rule, access=None):
        """A decorator that is used to register GET request handler.

        Example:
            @app.get('/some_url', access=['*'])
            def handler(): ...
        """
        return self.route(rule, access=access, methods=['GET'])

    def delete(self, rule, access=None):
        """A decorator that is used to register DELETE request handler.

        Example:
            @app.delete('/some_url', access=['*'])
            def handler(): ...
        """
        return self.route(rule, access=access, methods=['DELETE'])

    @staticmethod
    def wrap(app):
        """Add sessions and CORS requests support to the app."""
        settings = app.settings
        app = SessionMiddleware(app, settings.session)
        app = QuizMiddleware(app, settings.session['session.key'])
        return app

    def isAdmin(self):
        return self.session['user_type'] == 'admin'

    def getUserId(self, uid=None):
        """Get user ID based on uid value.

        If uid is None or 'me' then session's user ID will be returned,
        otherwise uid itself will be returned.
        """
        if uid is None or uid == 'me':
            return self.session['user_id']
        else:
            return long(uid)

    def getLang(self):
        """Get language based on query parameters.

        If *lang* parameter is provided then it will be returned,
        otherwise 'it' will be returned.
        """
        return self.request.args.get('lang', 'it')

    ### Default handlers

    def onNewAuth(self):
        """Handle 'New authorization' request.
        Return JSON with auth data.

        :seealso: :class:`QuizWWWAuthenticate`.
        """
        return JSONResponse(QuizWWWAuthenticate().to_dict(), status=401)

    def onDoAuth(self):
        """Handle authorization."""
        data = self.request.json
        try:
            nonce = data["nonce"]
            login = data["login"]
            appkey = data["appid"]
            digest = data["digest"]
        except KeyError:
            raise BadRequest('Invalid parameters.')

        try:
            appid = self.core.getAppId(appkey)
            user = self.core.getUserInfo(login, with_passwd=True)
        except QuizCoreError:
            raise BadRequest('Authorization is invalid.')

        if not _check_digest(nonce, digest, user['passwd']):
            raise BadRequest('Authorization is invalid.')

        self.session['app_id'] = appid
        self.session['user_id'] = user['id']
        self.session['user_name'] = user['name']
        self.session['user_login'] = user['login']
        self.session['user_type'] = user['type']
        self.session.save()
        del user['login']

        # NOTE: we you want to use 'beaker.session.secret' then use:
        # sid = self.session.__dict__['_headers']['cookie_out']
        # sid = sid[sid.find('=') + 1:sid.find(';')]
        sid = self.session.id

        return JSONResponse({'sid': sid, 'user': user})
