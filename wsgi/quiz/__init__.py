import os
import os.path
from werkzeug.routing import BaseConverter
from flask import session
from flask_principal import PermissionDenied
from .appcore import Application, json_response
from .core.exceptions import QuizCoreError
from .serviceproxy import AccountsApi

app = None
assets = None


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
    # Default initialization
    global app
    global assets
    app = Application(__name__)

    # Load configuration
    cfg_name = os.path.basename(main_config)
    local_cfg = os.path.join('../../local', cfg_name)
    app.load_config(main_config, extra_configs=[local_cfg, extra_config],
                    env_var='QUIZ_SETTINGS')

    # Core initialization
    app.init()
    assets = app.assets

    # Force Italian translations.
    # Also may be configured via BABEL_DEFAULT_LOCALE.
    # Docs: http://pythonhosted.org/Flask-BabelEx
    @app.babel.localeselector
    def get_locale():
        return "it"

    # application modules initialization
    init_app()

    # print app.url_map
    return app


def init_app():
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
    # build_only - because we need an endpoint to reference to images
    # in the templates, and files will be handled by apache or nginx.
    app.add_url_rule('/img/<filename>', 'img_file', build_only=True)

    debug = app.config.get('DEBUG', False)

    # for testing
    if debug is True:
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
    # from .ui import ui

    app.register_blueprint(login.login_api, url_prefix='/v1')
    app.register_blueprint(api, url_prefix='/v1')
    # app.register_blueprint(ui, url_prefix='/ui')

    init_quiz(app)

    # Like this we disable static files handing by flask on production
    # to test (and be sure) if apache (or nginx) serve them.
    # If apache/nginx configured wrongly then static files will not be
    # handled at all.
    # NOTE: for OpenShift all static files must be placed inside wsgi/static
    # to be correctly handled by apache (at least for python cartridge).
    # You need to add symlinks to wsgi/static if you have assets
    # in other locations in .openshift/action_hooks/deploy. For example:
    #
    #   ln -s $OPENSHIFT_REPO_DIR/wsgi/quiz/ui/static \
    #         $OPENSHIFT_REPO_DIR/wsgi/static/ui
    #
    # here we create symlink for frontend's static files, now apache will serve
    # urls like site.com/ui/static/ui/<path to asset>.
    if debug is False:
        for rule in app.url_map._rules:
            if rule.rule.startswith('/ui/static/ui'):
                rule.build_only = True


def init_quiz(app):
    from .assets import assets
    from . import quiz_b, quiz_cqc, quiz_am, quiz_truck

    assets.init_app(app)

    quiz_b.quiz.init_app(app, quiz_id=1, quiz_year=2011, base_prefix='/new')
    quiz_cqc.quiz.init_app(app, quiz_id=2, quiz_year=2011, base_prefix='/new')
    quiz_b.quiz.init_app(app, quiz_id=3, quiz_year=2013, base_prefix='/new')
    quiz_am.quiz.init_app(app, quiz_id=4, quiz_year=2013, base_prefix='/new')
    quiz_truck.quiz.init_app(app, quiz_id=5, quiz_year=2013, base_prefix='/new')
