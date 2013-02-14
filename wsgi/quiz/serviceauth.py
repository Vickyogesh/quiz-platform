import hashlib
import time
import random
from werkzeug.http import parse_dict_header
from werkzeug.wrappers import Response
from werkzeug.exceptions import BadRequest
from quiz.exceptions import QuizCoreError


class QuizWWWAuthenticate(object):
    """" Provides simple WWW-Authenticate header for the Quiz service. """

    def __init__(self):
        self.random = random.random()
        self.time = time.time()

    def to_header(self):
        """ Convert the stored values into a WWW-Authenticate header. """
        m = hashlib.md5()
        m.update('{0}:{1}'.format(self.random, self.time))
        return 'QuizAuth nonce="%s"' % m.hexdigest()


class QuizAuthorization(object):
    """"
    Represents an Authorization header sent by the client.
    Expected header format:
        QuizAuth nonce="...", appid="...", username="...", digest="..."
    """

    def __init__(self, header):
        """
        Construct object from the header text.
        If header is invalid then is_valid will be False.
        """
        try:
            self.header = self._parseHeader(header)
            self.appkey = self.header['appid']
            self.user = self.header['username']
            self.digest = self.header['digest']
            self.nonce = self.header['nonce']
            self.is_valid = True
        except KeyError:
            self.is_valid = False

    # helper function: removes leading "QuizAuth "
    # and parses header to the dict.
    def _parseHeader(self, header):
        if not header.startswith('QuizAuth '):
            raise KeyError
        else:
            return parse_dict_header(header[9:])


class AuthMixin(object):
    """
    This class provides authorization routines and used in the
    ServiceBase as a mixin.
    Authorization flow:
        * client send /authorize request
        * service send 401 response with the header:
            WWW-Authenticate: QuizAuth nonce="<value>"
        * client performs digest calculation using nonce:
            HA1 = BASE64( MD5(<username>:<password>) )
            DIGEST = BASE64( MD5(<nonce>:<HA1>) )
          and repeat /authorize request with the Authorization header:
            Authorization: QuizAuth nonce="<nonce>", appid="<id>",
                username="<name>", digest="<DIGEST>"
        * if authorization data is correct service send 200 OK
          and client can work with the service API.
    See QuizWWWAuthenticate and QuizAuthorization classes for more info.
    """

    def _check_digest(self, header, passwd):
        m = hashlib.md5()
        m.update('%s:%s' % (header.nonce, passwd))
        return m.hexdigest() == header.digest

    def _onValidateAuth(self, request):
        header = QuizAuthorization(request.headers.get('Authorization', ''))

        if not header.is_valid:
            raise BadRequest('Invalid parameters.')

        data = self.core.getUserAndAppInfo(header.user, header.appkey)

        if not data or not self._check_digest(header, data['passwd']):
            raise BadRequest('Authorization is invalid.')

        self.session['app_id'] = data['app_id']
        self.session['user_id'] = data['user_id']
        self.session['user_type'] = data['type']
        self.session.save()
        return Response()

    def _onNewAuth(self, request):
        header = {'WWW-Authenticate': QuizWWWAuthenticate().to_header()}
        return Response('401 Unauthorized', 401, headers=header)

    def on_authorize(self, request):
        if 'Authorization' in request.headers:
            return self._onValidateAuth(request)
        else:
            return self._onNewAuth(request)
