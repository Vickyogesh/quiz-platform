import os
from quiz.wsgi import QuizApp
from quiz.service import app as application
application = QuizApp.wrap(application)

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
