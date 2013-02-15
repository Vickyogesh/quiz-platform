from .service import QuizService
from beaker.middleware import SessionMiddleware
from werkzeug.wsgi import SharedDataMiddleware


def create_app(settings):
    app = QuizService(settings)
    app = SessionMiddleware(app, settings.session)
    if settings.testing.get('test_html', '') == 'True':
        import os.path
        path = os.path.join(os.path.dirname(__file__),
                            '..', '..', 'tests', 'static')
        path = os.path.abspath(path)
        print('Using html path: ' + path)
        app = SharedDataMiddleware(app, {'/test': path})
    return app
