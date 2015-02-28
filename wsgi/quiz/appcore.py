import traceback
import re
from datetime import date
from werkzeug.exceptions import HTTPException, BadRequest, default_exceptions
from flask import Flask, json, current_app, request, Request
from flask.ext.babelex import Babel, get_locale
from flask_beaker import BeakerSession
import flask_bootstrap


###########################################################
# JSON support.
###########################################################

class JSONEncoderEx(json.JSONEncoder):
    """Extends :class:`flask.json.JSONEncoder` with date-to-ISO string encoding.

    It used in :func:`jsonify_ex` to convert datetime objects.
    """
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


# Based on code from flask.jsonify().
def jsonify_ex(*args, **kwargs):
    """Extended version of :func:`flask.json.jsonify`
    which supports date objects.

    The arguments to this function are the same as to the dict constructor.

    See Also:
        :func:`json_response`.
    """
    indent = None
    if (current_app.config['JSONIFY_PRETTYPRINT_REGULAR']
       and not request.is_xhr):
        indent = 2

    s = json.dumps(dict(*args, **kwargs), cls=JSONEncoderEx, indent=indent)
    return current_app.response_class(s, mimetype='application/json')


def json_response(status=200, **kwargs):
    """Helper function for building JSON response with the given HTTP status.

    It also puts status to the JSON as `status` field.

    Args:
        status: HTTP response status code
        kwargs: keyword arguments to put in result JSON.

    Returns:
        :class:`flask.Response` with the JSON.

    See Also:
            :func:`jsonify_ex`
    """
    response = jsonify_ex(status=status, **kwargs)
    response.status_code = status
    return response


def dict_to_json_response(data, status=200):
    """Creates JSON response for :class:`dict`.

    Args:
        data: Dictionary to convert.
        status: Response status.

    See Also:
        :func:`jsonify_ex`.
    """
    return jsonify_ex(data, status=status)


class JsonRequest(Request):
    """This class changes :class:`flask.Request` behaviour on JSON parse error.

    If HTTP response doesn't contain JSON data and you call
    :samp:`request.get_json()` then :class:`~werkzeug.exceptions.BadRequest`
    will be raised.
    """
    def __init__(self, environ, populate_request=True, shallow=False):
        super(JsonRequest, self).__init__(environ, populate_request, shallow)

    def get_json(self, force=False, silent=False, cache=True):
        val = Request.get_json(self, force, silent, cache)
        if val is None and force:
            val = self.on_json_loading_failed(None)
        return val

    def on_json_loading_failed(self, e):
        raise BadRequest("Not a JSON.")


###########################################################
# Application.
###########################################################

class Application(Flask):
    """This class adds to the :class:`flask.Flask` JSON error handing
    and also performs core initialization.

    Initialization example::

        app = Application()
        app.load_config()
        app.init()

    Other initialization steps are performed in :func:`quiz.init_app`.
    """
    request_class = JsonRequest

    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(*args, **kwargs)
        self.__setup()

    @staticmethod
    def __json_error(e):
        if hasattr(e, "description"):
            status = e.code if isinstance(e, HTTPException) else 500
            if status == 401:
                desc = 'Unauthorized.'
            elif status == 403:
                desc = 'Forbidden.'
            elif status == 405:
                desc = 'Not Allowed.'
            else:
                desc = e.description
            return json_response(status, description=desc)
        else:
            traceback.print_exc()
            return json_response(500)

    # Make all errors in JSON format except HTTP 404.
    def __setup(self):
        for code in default_exceptions.iterkeys():
            if code != 404:
                self.error_handler_spec[None][code] = Application.__json_error

    def __setup_bootstrap(self):
        flask_bootstrap.Bootstrap(self)
        ver = re.sub(r'^(\d+\.\d+\.\d+).*', r'\1', flask_bootstrap.__version__)
        cdn = self.extensions['bootstrap']['cdns']['bootstrap']
        cdn.fallback.baseurl = '//maxcdn.bootstrapcdn.com/bootstrap/%s/' % ver

        # http://blog.jquery.com/2014/12/18/jquery-1-11-2-and-2-1-3-released-safari-fail-safe-edition/
        cdn = self.extensions['bootstrap']['cdns']['jquery']
        cdn.fallback.baseurl = '//cdnjs.cloudflare.com/ajax/libs/jquery/2.1.3/'

    def load_config(self, config_path, extra_configs=None, env_var=None):
        """Load application configurations.

        It loads configurations in the following order:
            * from the `config_path`;
            * from the list `extra_configs`;
            * from the the `env_var`;

        This method will fails only if configuration from `config_path`
        can't be loaded.

        Args:
            config_path: Main configuration file path.
            extra_configs: Optional list of additional file paths or objects
                           to load from.
            env_var: Optional environment variable with file path.
        """
        self.config.from_pyfile(config_path)

        if extra_configs is not None:
            for cfg in extra_configs:
                if isinstance(cfg, str) or isinstance(cfg, unicode):
                    self.config.from_pyfile(cfg, silent=True)
                elif isinstance(cfg, object):
                    self.config.from_object(cfg)

        if env_var is not None:
            self.config.from_envvar(env_var, silent=True)

    def init(self):
        """Basic initialization.

        This method initialize 3rd party extensions, access control routines
        and accounts API:

        * Beaker session.
        * Babel (localization).
        * Bootstrap.
        * Templates language.
        """
        BeakerSession(self)
        self.babel = Babel(self)
        self.__setup_bootstrap()

        # Inject current language to the template context.
        @self.context_processor
        def inject_lang():
            return dict(current_lang=get_locale().language)
