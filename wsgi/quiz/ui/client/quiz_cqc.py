from ..page import PageModels
from .models import MenuModel, QuizMenuModel, ExamModel


class CqcModel(MenuModel):
    template = 'ui/cqc/menu_client.html'


class CqcQuizMenuModel(QuizMenuModel):
    template = 'ui/cqc/menu_quiz.html'


class CqcExamModel(ExamModel):
    template = 'ui/cqc/exam.html'
    exam_meta = {'max_errors': 6, 'total_time': 7200}


class CqcPageModels(PageModels):
    name = 'cqc'
    standard_page_models = {
        'menu': CqcModel,
        'menu_quiz': CqcQuizMenuModel,
        'exam': CqcExamModel,
        # these pages will use default models.
        # 'quiz': CommonModel,
        # 'review': CommonModel,
        # 'stat': CommonModel,
        # 'topic_stat': CommonModel,
        # 'exam_stat': CommonModel
    }
