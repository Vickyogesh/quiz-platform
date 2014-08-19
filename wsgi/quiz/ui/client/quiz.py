from flask import url_for, request
from ..page import PageModel, ClientPage
from ... import app


############################################################
# Models
############################################################

class BaseQuizModel(PageModel):
    def get_quiz(self, *args, **kwargs):
        raise NotImplemented

    def on_request(self, *args, **kwargs):
        self.page.urls = {
            'back': url_for('.client_menu'),
            'image': url_for('img_file', filename='')
        }
        info = self.get_quiz(*args, **kwargs)
        return self.page.render(quiz=info)


class QuizModel(BaseQuizModel):
    template = 'ui/common_quiz.html'

    def get_quiz(self, topic):
        force = request.args.get('force', False)

        # TODO: what if x is not int?
        exclude = request.args.get('exclude', None)
        if exclude is not None:
            exclude = [int(x) for x in exclude.split(',')]

        self.page.urls['quiz'] = url_for('api.create_quiz', topic=0)[:-1]
        return app.core.getQuiz(self.page.quiz_id, self.page.uid, topic,
                                self.page.lang, force, exclude)


class ReviewModel(BaseQuizModel):
    """Error review."""
    template = 'ui/common_review.html'

    def get_quiz(self):
        # TODO: what if x is not int?
        exclude = request.args.get('exclude', None)
        if exclude is not None:
            exclude = [int(x) for x in exclude.split(',')]

        self.page.urls['quiz'] = url_for('api.get_error_review')
        return app.core.getErrorReview(self.page.quiz_id, self.page.uid,
                                       self.page.lang, exclude)


############################################################
# View
############################################################

class Quiz(ClientPage):
    models = {'':  QuizModel}


class Review(ClientPage):
    models = {'': ReviewModel}
