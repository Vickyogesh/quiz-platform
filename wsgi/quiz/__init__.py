import os
import os.path
from werkzeug.routing import BaseConverter
from flask import session
from flask_principal import PermissionDenied
from .appcore import Application, json_response
from .core.exceptions import QuizCoreError
from .serviceproxy import AccountsApi
from raven.contrib.flask import Sentry

app = None


class IdConverter(BaseConverter):
    """int or 'me' identifiers to use in Rules."""
    def __init__(self, url_map):
        super(IdConverter, self).__init__(url_map)
        self.regex = '(?:me|\d+)'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


class WordConverter(BaseConverter):
    """Alphanumeric identifiers to use in Rules."""
    def __init__(self, url_map):
        super(WordConverter, self).__init__(url_map)
        self.regex = '\w+'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


def create_app(main_config='../../misc/quiz.cfg', extra_config=None):
    """Application factory function.

    It creates and configures **Quiz Service** WSGI application.

    Configuration is loaded in the following order:

    * :file:`misc/quiz.cfg`
    * :file:`local/quiz.cfg`
    * ``extra_config``
    * :envvar:`QUIZ_SETTINGS` environment variable

    Args:
        extra_config: extra configuration.

    Returns:
        **Quiz Service** WSGI application.

    See Also:
        :func:`init_app`.
    """
    # Default initialization
    global app
    app = Application(__name__)

    # Load configuration
    cfg_name = os.path.basename(main_config)
    local_cfg = os.path.join('../../local', cfg_name)
    app.load_config(main_config, extra_configs=[local_cfg, extra_config],
                    env_var='QUIZ_SETTINGS')

    # Core initialization
    app.init()

    # Force Italian translations.
    # Also may be configured via BABEL_DEFAULT_LOCALE.
    # Docs: http://pythonhosted.org/Flask-BabelEx
    @app.babel.localeselector
    def get_locale():
        return "it"

    # application modules initialization
    init_app()
    return app


def init_app():
    """Application initialization.

    This function gets called in :func:`create_app` as a last step.

    It performs the following actions:

    * Extra errors handlers setup.
    * Static files URL riles setup.
    * :class:`.AccountsApi` setup.
    * Backend logic setup.
    * Frontends and web API setup.
    """
    def core_error_handler(error):
        return json_response(status=400, description=error.message)

    def permission_denied_handler(error):
        return "Forbidden. <a href='https://quiz.editricetoni.it/new/session_clean'>Logout</a>"
        # return json_response(status=403, description='Forbidden.')

    def sess():
        return session

    app.url_map.converters['uid'] = IdConverter
    app.url_map.converters['word'] = WordConverter

    app.errorhandler(QuizCoreError)(core_error_handler)
    app.errorhandler(PermissionDenied)(permission_denied_handler)

    # Accounts proxy setup.
    url = app.config['ACCOUNTS_URL']
    domain = app.config.get('ACCOUNTS_COOKIE_DOMAIN')
    app.account = AccountsApi(url, session_func=sess, call_save=False,
                              target_cookie_domain=domain)
    # build_only - because we need an endpoint to reference to images
    # in the templates, and files will be handled by apache or nginx.
    app.add_url_rule('/img/<filename>', 'img_file', build_only=True)

    # for testing
    if app.debug:
        import os.path
        from werkzeug import SharedDataMiddleware
        here = os.path.dirname(__file__)
        b2013 = os.path.join(here, '../..', 'web', 'b2013')
        cqc = os.path.join(here, '../..', 'web', 'cqc')
        app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
            '/img':  app.config['DATA_DIR'] + '/img',
            '/b2013': b2013,
            '/cqc': cqc
        })

    # Logic setup
    from .core.core import QuizCore
    app.core = QuizCore(app)

    from . import access
    from . import login
    from .api import api
    from .core2.bp import core2
    from .core2.models import db
    from .content_manager import cm
    from .assets import assets

    app.register_blueprint(login.login_api, url_prefix='/v1')
    app.register_blueprint(api, url_prefix='/v1')
    app.register_blueprint(cm, url_prefix='/cm')
    app.register_blueprint(core2, url_prefix='/new')
    assets.init_app(app)
    db.init_app(app)
    sentry = Sentry(app)

    from . import views
