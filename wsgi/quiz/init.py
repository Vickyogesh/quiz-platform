from werkzeug.routing import BaseConverter
from flask import session
from flask_principal import PermissionDenied
from .appcore import json_response
from .core.exceptions import QuizCoreError
from .serviceproxy import AccountsApi


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


def init_app(app):
    def core_error_handler(error):
        return json_response(status=400, description=error.message)

    def permission_denied_handler(error):
        return json_response(status=403, description='Forbidden.')

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

    app.add_url_rule('/img/<filename>', 'img_file', build_only=True)

    # for testing
    if app.config.get('DEBUG', False) is True:
        import os.path
        from werkzeug import SharedDataMiddleware
        here = os.path.dirname(__file__)
        b2013 = os.path.join(here, '../..', 'web', 'b2013')
        app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
            '/img':  app.config['DATA_DIR'] + '/img',
            '/b2013': b2013
        })

    # Logic setup
    from .core.core import QuizCore
    app.core = QuizCore(app)

    from . import access
    from . import login
    from .api import api
    from .ui import ui

    app.register_blueprint(login.login_api, url_prefix='/v1')
    app.register_blueprint(api, url_prefix='/v1')
    app.register_blueprint(ui, url_prefix='/ui')
