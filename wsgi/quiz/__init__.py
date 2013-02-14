from .service import QuizService
from beaker.middleware import SessionMiddleware


def create_app(settings):
    app = QuizService(settings)
    return SessionMiddleware(app, settings.session)
