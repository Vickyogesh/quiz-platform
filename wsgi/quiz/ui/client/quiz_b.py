from ..page import PagesMetadata
from .models import MenuModel, QuizMenuModel, ExamModel, StatisticsModel

exam_meta = {'max_errors': 4, 'total_time': 1800, 'num_questions': 40}


class BModel(MenuModel):
    template = 'ui/b/menu_client.html'


class BQuizMenuModel(QuizMenuModel):
    template = 'ui/b/menu_quiz.html'


class BExamModel(ExamModel):
    template = 'ui/b/exam.html'
    exam_meta = exam_meta


class BStatisticsModel(StatisticsModel):
    exam_meta = exam_meta


class BPagesMetadata(PagesMetadata):
    name = 'b'
    standard_page_models = {
        'menu': BModel,
        'menu_quiz': BQuizMenuModel,
        'exam': BExamModel,
        'stat': BStatisticsModel
    }
