from werkzeug.urls import url_decode


# TODO: maybe analyse:
#  HTTP_ACCESS_CONTROL_REQUEST_HEADERS content-type
#  HTTP_ACCESS_CONTROL_REQUEST_METHOD GET
class QuizMiddleware(object):
    """ This middleware provides CORS Preflight requests handling
    and embedding seassion ID to the WSGI environment.
    """
    # 1728000 sec = 20 days
    def __init__(self, app, cookie_key, url_key='sid', timeout=1728000):
        """ Initialize middleware.

        Args:
            :param cookie_key:  cookie name to embed.
            :param url_key:     URL param name which must be embedded as cookie.
            :param timeout:     CORS Preflight request timeout in seconds.


        CORS support
        ------------

        To provide cross-origin requests server must handle
        CORS preflight request like:

            OPTIONS /path HTTP/1.1
            Origin: http://example.com
            Access-Control-Request-Method: GET
            Access-Control-Request-Headers: content-type

        QuizMiddleware will send the following preflight response:

            Access-Control-Allow-Origin: *
            Access-Control-Allow-Methods: GET, POST, OPTIONS
            Access-Control-Allow-Headers: content-type
            Content-Type: text/html; charset=utf-8
            Access-Control-Max-Age: <timeout>

        Note what with "Access-Control-Allow-Origin: *" we can't use
        "Access-Control-Allow-Credentials: true" to allow cookies processing.

        For more info see:
            http://www.html5rocks.com/en/tutorials/cors
            https://developer.mozilla.org/en-US/docs/HTTP/Access_control_CORS


        Cookie embedding
        ----------------

        Since we can't work with cookies (see CORS support section) then
        to support beaker session middleware we need to embedd session ID to
        the *HTTP_COOKIE* WSGI environment.

        To support sessions for the CORS requests we pass session id in the
        URL query parameter 'sid' and then set session cookie. Thus beaker
        middleware will be able to extract session cookies from the HTTP_COOKIE
        variable.
        """
        self.app = app
        self._cookie_key = cookie_key
        self._url_key = url_key
        self._url_key_check = url_key + '='
        self._timeout = str(timeout)

    def __call__(self, environ, start_response):
        if environ.get('REQUEST_METHOD') == 'OPTIONS':
            headers = [
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
                ('Access-Control-Allow-Headers', 'content-type'),
                ('Content-Type', 'text/html; charset=utf-8'),
                ('Access-Control-Max-Age', self._timeout),
                ('Content-Length', '0')
            ]
            start_response('200 OK', headers)
            return ''

        # TODO: maybe replace url_decode() with simple search?
        # If url contains self.url_key then we need to embed cookie
        query = environ.get('QUERY_STRING')
        if self._url_key_check in query:
            q = url_decode(query)
            sid = q[self._url_key]
            environ["HTTP_COOKIE"] = str(self._cookie_key + "=" + sid)
        return self.app(environ, start_response)
