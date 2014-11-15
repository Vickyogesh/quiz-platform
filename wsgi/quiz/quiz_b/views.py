from ..common.views import ClientView, ClientFullscreenView
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


@quiz.view
class ClientReview(ClientView):
    template_name = 'common_review.html'


@quiz.view
class ClientStatistics(ClientView):
    template_name = 'statistics_client.html'


@quiz.view
class ClientExam(ClientView):
    template_name = 'quiz_b/exam.html'


@quiz.route('/school/menu')
def school_menu():
    return "school_menu"
