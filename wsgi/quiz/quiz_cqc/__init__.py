"""
This package implements Quiz CQC.
"""
from flask_babelex import lazy_gettext
from ..common.base import Bundle
from ..common import client_views, school_views, index

quiz = Bundle(__name__, {
    'name': 'cqc',
    'title': lazy_gettext('CQC'),
    'exam_meta': {'max_errors': 6, 'total_time': 7200, 'num_questions': 60}
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
        # We have to send 'cqc' to the Accounts Service instead of cqc2011.
        year = self.meta['year']
        if year == 2011:
            return self.meta['name']
        else:
            return ''.join((self.meta['name'], str(year)))


@quiz.view
class ClientMenu(client_views.ClientView):
    template_name = 'quiz_cqc/menu_client.html'


@quiz.view
class ClientMenuQuiz(client_views.ClientTopicsView):
    template_name = 'quiz_cqc/menu_topics.html'


@quiz.view
class ClientExam(client_views.ClientExamView):
    template_name = 'quiz_cqc/exam.html'
