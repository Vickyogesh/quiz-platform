from .service import QuizService
from .middleware import QuizMiddleware
from beaker.middleware import SessionMiddleware


def create_app(settings):
    app = QuizService(settings)
    app = SessionMiddleware(app, settings.session)
    app = QuizMiddleware(app, settings.session['session.key'])
    return app
