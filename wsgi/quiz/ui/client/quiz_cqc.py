from ..page import PagesMetadata
from .models import MenuModel, QuizMenuModel, ExamModel, StatisticsExamsModel, StatisticsModel

exam_meta = {'max_errors': 6, 'total_time': 7200, 'num_questions': 60}

class CqcModel(MenuModel):
    template = 'ui/cqc/menu_client.html'


class CqcQuizMenuModel(QuizMenuModel):
    template = 'ui/cqc/menu_quiz.html'


class CqcExamModel(ExamModel):
    template = 'ui/cqc/exam.html'
    exam_meta = exam_meta


class CqcStatisticsExamsModel(StatisticsExamsModel):
    num_exam_questions = exam_meta['num_questions']


class CqcStatisticsModel(StatisticsModel):
    exam_meta = exam_meta


class CqcPagesMetadata(PagesMetadata):
    name = 'cqc'
    standard_page_models = {
        'menu': CqcModel,
        'menu_quiz': CqcQuizMenuModel,
        'exam': CqcExamModel,
        'exam_stat': CqcStatisticsExamsModel,
        'stat': CqcStatisticsModel
    }