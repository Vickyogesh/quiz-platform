from .models import (
    QuizMenuModel,
    MenuModel,
    QuizModel,
    ReviewModel,
    ExamModel,
    ExamReviewModel,
    StatisticsModel,
    StatisticsTopicModel,
    StatisticsExamsModel
)
from ..page import PageView
from ... import access


class ClientPage(PageView):
    """Base class for client's page views.

    It sets endpoint prefix and common decorator to control access.
    """
    decorators = [access.be_client_or_guest.require()]
    endpoint_prefix = 'client'


class MenuView(ClientPage):
    rules = ({'rule': '/c/menu'},)
    default_model = MenuModel


class MenuQuizView(ClientPage):
    rules = ({'rule': '/c/menu/quiz'},)
    default_model = QuizMenuModel


class QuizView(ClientPage):
    rules = ({'rule': '/c/quiz/<int:topic>'},)
    default_model = QuizModel


class ReviewView(ClientPage):
    rules = ({'rule': '/c/review'},)
    default_model = ReviewModel


class ExamView(ClientPage):
    rules = ({'rule': '/c/exam'},)
    default_model = ExamModel


class ExamReviewView(ClientPage):
    rules = ({'rule': '/c/exam_review/<int:id>'},)
    default_model = ExamReviewModel


class StatisticsPage(ClientPage):
    decorators = [access.be_user.require()]


class StatisticsView(StatisticsPage):
    rules = (
        {'rule': '/c/statistics', 'defaults': {'uid': 'me'}},
        {'rule': '/c/statistics/<uid:uid>'}
    )
    default_model = StatisticsModel


class StatisticsTopicView(StatisticsPage):
    rules = ({'rule': '/c/statistics/<uid:uid>/topic/<int:topic_id>'},)
    default_model = StatisticsTopicModel


class StatisticsExamsView(StatisticsPage):
    rules = ({'rule': '/c/statistics/<uid:uid>/exams/<range>'},)
    default_model = StatisticsExamsModel


# Client pages.
# Used in __init__.py by page.register_pages().
page_views = {
    'menu': MenuView,
    'menu_quiz': MenuQuizView,
    'quiz': QuizView,
    'review': ReviewView,
    'exam': ExamView,
    'exam_review': ExamReviewView,
    'stat': StatisticsView,
    'topic_stat': StatisticsTopicView,
    'exam_stat': StatisticsExamsView
}
