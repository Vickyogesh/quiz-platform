"""
This package implements Quiz B.
"""
from flask_babelex import lazy_gettext
from ..common.base import Bundle
from ..common import client_views, school_views, index

quiz = Bundle(__name__, {
    'name': 'b',
    'title': lazy_gettext('Quiz B'),
    'exam_meta': {'max_errors': 4, 'total_time': 1800, 'num_questions': 40}
})

# -- Common views --------------------------------------------------------------

quiz.view(index.IndexView)
quiz.view(index.VideoView)
quiz.view(client_views.ClientQuizView)
quiz.view(client_views.ClientReviewView)
quiz.view(client_views.ClientExamReviewView)
quiz.view(client_views.ClientStatisticsView)
quiz.view(client_views.ClientTopicStatisticsView)
quiz.view(client_views.ClientExamStatisticsView)

quiz.view(school_views.SchoolMenuView)
quiz.view(school_views.SchoolStatisticsView)


# -- Quiz specific views -------------------------------------------------------

@quiz.view
class ClientMenu(client_views.ClientMenuView):
    template_name = 'quiz_b/menu_client.html'


@quiz.view
class ClientMenuQuiz(client_views.ClientTopicsView):
    template_name = 'quiz_b/menu_topics.html'


@quiz.view
class ClientExam(client_views.ClientExamView):
    template_name = 'quiz_b/exam.html'
