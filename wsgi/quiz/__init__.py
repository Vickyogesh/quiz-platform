from .service import QuizService
from beaker.middleware import SessionMiddleware


def create_app(settings):
    app = QuizService(settings)
    app = SessionMiddleware(app, settings.session)
    return app
