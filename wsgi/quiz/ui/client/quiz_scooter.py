from ..page import PagesMetadata
from .models import QuizMenuModel, ExamModel, StatisticsExamsModel, StatisticsModel
from .quiz_b import BModel

exam_meta = {'max_errors': 3, 'total_time': 1500, 'num_questions': 30}

class ScooterModel(BModel):
    pass


class ScooterQuizMenuModel(QuizMenuModel):
    template = 'ui/scooter/menu_quiz.html'


class ScooterExamModel(ExamModel):
    template = 'ui/scooter/exam.html'
    exam_meta = exam_meta


class ScooterStatisticsExamsModel(StatisticsExamsModel):
    num_exam_questions = exam_meta['num_questions']


class ScooterStatisticsModel(StatisticsModel):
    exam_meta = exam_meta


class ScooterPagesMetadata(PagesMetadata):
    name = 'am'
    standard_page_models = {
        'menu': ScooterModel,
        'menu_quiz': ScooterQuizMenuModel,
        'exam': ScooterExamModel,
        'exam_stat': ScooterStatisticsExamsModel,
        'stat': ScooterStatisticsModel
    }
