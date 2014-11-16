"""
This package implements Quiz CQC.
"""
from flask_babelex import lazy_gettext
from ..common.base import Bundle
from ..common import client_views, school_views, index

quiz = Bundle(__name__, {
    'name': 'am',
    'title': lazy_gettext('Scooter'),
    'exam_meta': {'max_errors': 3, 'total_time': 1500, 'num_questions': 30}
})


# -- Common views --------------------------------------------------------------

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
class IndexView(index.IndexView):
    @property
    def quiz_fullname(self):
        # For backward compatibility.
        # We have to send 'scooter' to the Accounts Service instead of
        # scooter2013.
        year = self.meta['year']
        if year == 2013:
            return self.meta['name']
        else:
            return ''.join((self.meta['name'], str(year)))


@quiz.view
class ClientMenu(client_views.ClientMenuView):
    template_name = 'quiz_b/menu_client.html'


@quiz.view
class ClientMenuQuiz(client_views.ClientTopicsView):
    template_name = 'quiz_am/menu_topics.html'


@quiz.view
class ClientExam(client_views.ClientExamView):
    template_name = 'quiz_am/exam.html'
