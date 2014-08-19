from ..page import PagesMetadata
from .models import MenuModel, QuizMenuModel, ExamModel


class BModel(MenuModel):
    template = 'ui/b/menu_client.html'


class BQuizMenuModel(QuizMenuModel):
    template = 'ui/b/menu_quiz.html'


class BExamModel(ExamModel):
    template = 'ui/b/exam.html'
    exam_meta = {'max_errors': 4, 'total_time': 1800}


class BPagesMetadata(PagesMetadata):
    name = 'b'
    standard_page_models = {
        'menu': BModel,
        'menu_quiz': BQuizMenuModel,
        'exam': BExamModel
    }
