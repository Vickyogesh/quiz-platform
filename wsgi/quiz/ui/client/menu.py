# coding=utf-8
from flask import url_for
from ..page import PageModel, ClientPage
from ..util import account_url


############################################################
# Models
############################################################

class MenuModel(PageModel):
    def on_request(self, *args, **kwargs):
        self.page.urls = {'account': account_url()}
        return PageModel.on_request(self, *args, **kwargs)


class BModel(MenuModel):
    template = 'ui/b/menu_client.html'


class ScooterModel(BModel):
    pass


class CqcModel(MenuModel):
    template = 'ui/cqc/menu_client.html'


class QuizMenuModel(PageModel):
    def on_request(self, *args, **kwargs):
        self.page.urls = {
            'back': url_for('.client_menu'),
            'quiz': url_for('.client_quiz', topic=0)[:-1],
            'account': account_url()
        }
        return PageModel.on_request(self, *args, **kwargs)


class BQuizMenuModel(QuizMenuModel):
    template = 'ui/b/menu_quiz.html'


class CqcQuizMenuModel(QuizMenuModel):
    template = 'ui/cqc/menu_quiz.html'


class ScooterQuizMenuModel(QuizMenuModel):
    template = 'ui/scooter/menu_quiz.html'


############################################################
# View
############################################################

class Menu(ClientPage):
    models = {
        'b': BModel,
        'cqc': CqcModel,
        'scooter': ScooterModel
    }


class MenuQuiz(ClientPage):
    models = {
        'b': BQuizMenuModel,
        'cqc': CqcQuizMenuModel,
        'scooter': ScooterQuizMenuModel
    }
