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
    img_path = os.path.join(here, '..', 'test-data', 'img')
    b2011 = os.path.join(here, '..', 'web', 'b2011')
    b2013 = os.path.join(here, '..', 'web', 'b2013')
    cqc = os.path.join(here, '..', 'web', 'cqc')
    config_file = os.path.join(here, '..', 'test-data', 'config.ini')

    application = DispatcherMiddleware(application, {'/v1': application})
    application = SharedDataMiddleware(application, {'/img': img_path})
    application = SharedDataMiddleware(application, {'/test': static_path})
    application = SharedDataMiddleware(application, {'/b2011': b2011})
    application = SharedDataMiddleware(application, {'/b2013': b2013})
    application = SharedDataMiddleware(application, {'/cqc': cqc})

    run_simple('192.168.43.1', 80, application, use_debugger=True,
               use_reloader=True,
               extra_files=[config_file])
