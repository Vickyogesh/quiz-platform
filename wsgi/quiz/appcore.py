import traceback
import re
from datetime import date
from werkzeug.exceptions import HTTPException, BadRequest, default_exceptions
from flask import Flask, json, current_app, request, Request
from flask.ext.babelex import Babel, get_locale
from flask.ext.assets import Environment
from flask_beaker import BeakerSession
import flask_bootstrap


###########################################################
# JSON support.
###########################################################

class JSONEncoderEx(json.JSONEncoder):
    """Extends JSONEncoder with date to ISO string encoding."""
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


# Based on code from flask.jsonify().
def jsonify_ex(*args, **kwargs):
    """Extended version of flask.jsonify() which supports date objects."""
    indent = None
    if (current_app.config['JSONIFY_PRETTYPRINT_REGULAR']
       and not request.is_xhr):
        indent = 2

    s = json.dumps(dict(*args, **kwargs), cls=JSONEncoderEx, indent=indent)
    return current_app.response_class(s, mimetype='application/json')


def json_response(status=200, **kwargs):
    response = jsonify_ex(status=status, **kwargs)
    response.status_code = status
    return response


def dict_to_json_response(data, status=200):
    return jsonify_ex(data, status=status)


class JsonRequest(Request):
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
        and accounts API.
        """
        BeakerSession(self)
        self.babel = Babel(self)
        self.assets = Environment(self)
        self.__setup_bootstrap()

        # Inject current language to the template context.
        @self.context_processor
        def inject_lang():
            return dict(curent_lang=get_locale().language)
