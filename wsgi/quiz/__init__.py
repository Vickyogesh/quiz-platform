import os
import os.path
from .appcore import Application

app = None
assets = None


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
    from .init import init_app
    init_app(app)

    # print app.url_map
    return app
