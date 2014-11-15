from flask import url_for, request, current_app
from flask_login import current_user
from ..common.views import ClientView
from ..common import index
from .bundle import quiz


@quiz.view
class IndexView(index.IndexView):
    pass


@quiz.view
class ClientMenu(ClientView):
    template_name = 'quiz_b/menu_client.html'


@quiz.view
class ClientMenuQuiz(ClientView):
    template_name = 'quiz_b/menu_quiz.html'

    def page_urls(self):
        return {
            'back': url_for('.client_menu'),
            'quiz': url_for('.client_quiz', topic=0)[:-1],
            'account': ClientView.account_url()
        }


class BaseQuiz(ClientView):
    def page_urls(self):
        return {
            'back': url_for('.client_menu'),
            'image': url_for('img_file', filename='')
        }

    def dispatch_request(self, *args, **kwargs):
        """Render template on request."""
        return self.render_template(quiz=self.get_quiz(*args, **kwargs))

    def get_quiz(self, *args, **kwargs):
        """Return questions for quiz/review.

        Must be overridden in subclass.
        """
        raise NotImplemented


@quiz.view
class ClientQuiz(BaseQuiz):
    template_name = 'common_quiz.html'
    url_rule = '/quiz/<int:topic>'

    def page_urls(self):
        urls = BaseQuiz.page_urls(self)
        urls['quiz'] = url_for('api.create_quiz', topic=0)[:-1]
        return urls

    def get_quiz(self, topic):
        force = request.args.get('force', False)
        lang = request.args.get('lang', 'it')
        uid = current_user.account_id

        # TODO: what if x is not int?
        exclude = request.args.get('exclude', None)
        if exclude is not None:
            exclude = [int(x) for x in exclude.split(',')]

        return current_app.core.getQuiz(self.meta['id'], uid, topic, lang,
                                        force, exclude)


@quiz.view
class ClientReview(BaseQuiz):
    template_name = 'common_review.html'

    def page_urls(self):
        urls = BaseQuiz.page_urls(self)
        urls['quiz'] = url_for('api.get_error_review')
        return urls

    def get_quiz(self):
        lang = request.args.get('lang', 'it')
        uid = current_user.account_id

        # TODO: what if x is not int?
        exclude = request.args.get('exclude', None)
        if exclude is not None:
            exclude = [int(x) for x in exclude.split(',')]

        return current_app.core.getErrorReview(self.meta['id'], uid, lang,
                                               exclude)


@quiz.view
class ClientStatistics(ClientView):
    template_name = 'statistics_client.html'


@quiz.view
class ClientExam(ClientView):
    template_name = 'quiz_b/exam.html'


@quiz.route('/school/menu')
def school_menu():
    return "school_menu"
