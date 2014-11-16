from ..common import views
from ..common import index
from .bundle import quiz


quiz.view(views.ClientQuizView)
quiz.view(views.ClientReviewView)
quiz.view(views.ClientExamReviewView)
quiz.view(views.ClientStatisticsView)
quiz.view(views.ClientTopicStatisticsView)
quiz.view(views.ClientExamStatisticsView)

@quiz.view
class IndexView(index.IndexView):
    pass


@quiz.view
class ClientMenu(views.ClientView):
    template_name = 'quiz_b/menu_client.html'


@quiz.view
class ClientMenuQuiz(views.ClientTopicsView):
    template_name = 'quiz_b/menu_quiz.html'


@quiz.view
class ClientExam(views.ClientExamView):
    template_name = 'quiz_b/exam.html'


@quiz.route('/school/menu')
def school_menu():
    return "school_menu"
