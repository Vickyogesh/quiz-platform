from ..common import client_views
from ..common import index
from .bundle import quiz


quiz.view(client_views.ClientQuizView)
quiz.view(client_views.ClientReviewView)
quiz.view(client_views.ClientExamReviewView)
quiz.view(client_views.ClientStatisticsView)
quiz.view(client_views.ClientTopicStatisticsView)
quiz.view(client_views.ClientExamStatisticsView)

@quiz.view
class IndexView(index.IndexView):
    pass


@quiz.view
class ClientMenu(client_views.ClientView):
    template_name = 'quiz_b/menu_client.html'


@quiz.view
class ClientMenuQuiz(client_views.ClientTopicsView):
    template_name = 'quiz_b/menu_topics.html'


@quiz.view
class ClientExam(client_views.ClientExamView):
    template_name = 'quiz_b/exam.html'


@quiz.route('/school/menu')
def school_menu():
    return "school_menu"
