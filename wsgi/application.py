from quiz import create_app
from quiz.settings import Settings
import os


# Construct list of paths where to search confguration.
# Search paths are:
#   $OPENSHIFT_DATA_DIR/quiz
#   ../test-data
def get_config_paths():
    import os.path
    oshift_path = os.getenv('OPENSHIFT_DATA_DIR', '')
    oshift_path = os.path.join(oshift_path, 'quiz')
    oshift_path = os.path.normpath(oshift_path)

    path = os.path.dirname(__file__)
    path = os.path.join(path, '..', 'test-data')
    path = os.path.normpath(path)

    return [oshift_path, path]

settings = Settings(get_config_paths())
application = create_app(settings)


if __name__ == '__main__':
    from werkzeug.serving import run_simple
    from werkzeug.wsgi import SharedDataMiddleware
    from werkzeug.wsgi import DispatcherMiddleware
    import os.path

    here = os.path.dirname(__file__)
    static_path = os.path.join(here, '..', 'tests', 'static')
    config_file = os.path.join(here, '..', 'test-data', 'config.ini')

    application = DispatcherMiddleware(application, {'/v1': application})
    application = SharedDataMiddleware(application, {'/test': static_path})

    run_simple('127.0.0.1', 80, application, use_debugger=True,
               use_reloader=True,
               extra_files=[config_file])
