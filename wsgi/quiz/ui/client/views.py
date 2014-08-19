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
from ..page import ClientPage

############################################################
# Base class for quiz page views.
############################################################


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


class StatisticsView(ClientPage):
    rules = (
        {'rule': '/c/statistics', 'defaults': {'uid': 'me'}},
        {'rule': '/c/statistics/<uid:uid>'}
    )
    default_model = StatisticsModel


class StatisticsTopicView(ClientPage):
    rules = ({'rule': '/c/statistics/<uid:uid>/topic/<int:topic_id>'},)
    default_model = StatisticsTopicModel


class StatisticsExamsView(ClientPage):
    rules = ({'rule': '/c/statistics/<uid:uid>/exams/<range>'},)
    default_model = StatisticsExamsModel


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
