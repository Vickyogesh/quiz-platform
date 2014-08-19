from ..page import PagesMetadata
from .models import QuizMenuModel, ExamModel
from .quiz_b import BModel


class ScooterModel(BModel):
    pass


class ScooterQuizMenuModel(QuizMenuModel):
    template = 'ui/scooter/menu_quiz.html'


class ScooterExamModel(ExamModel):
    template = 'ui/scooter/exam.html'
    exam_meta = {'max_errors': 3, 'total_time': 1500}


class ScooterPagesMetadata(PagesMetadata):
    name = 'scooter'
    standard_page_models = {
        'menu': ScooterModel,
        'menu_quiz': ScooterQuizMenuModel,
        'exam': ScooterExamModel,
        # these pages will use default models.
        # 'quiz': CommonModel,
        # 'review': CommonModel,
        # 'stat': CommonModel,
        # 'topic_stat': CommonModel,
        # 'exam_stat': CommonModel
    }
