from flask import url_for, request, abort
from .page import Page
from .util import account_url
from .. import access, app


def register_urls_for(bp):
    bp.route('/c/menu')(Menu.get_view())
    bp.route('/c/menu/quiz')(MenuQuiz.get_view())
    bp.route('/c/quiz/<int:topic>')(Quiz.get_view())
    bp.route('/c/review')(Review.get_view())
    bp.route('/c/exam')(Exam.get_view())
    bp.route('/c/exam_review/<int:id>')(ExamReview.get_view())

    bp.route('/c/statistics')(Statistics.get_view())
    bp.route('/c/statistics/topic/<int:topic_id>')(StatisticsTopic.get_view())
    bp.route('/c/statistics/exams/<range>')(StatisticsExams.get_view())


### Client only pages

class ClientPage(Page):
    decorators = [access.be_client_or_guest.require()]
    endpoint_prefix = 'client'


class Menu(ClientPage):
    template_name = 'ui/menu_client.html'

    def on_request(self):
        self.urls = {'account': account_url()}
        return self.render()


class MenuQuiz(ClientPage):
    template_name = 'ui/menu_quiz.html'

    def on_request(self):
        quiz_url = url_for('.client_quiz', topic=0)[:-1]
        self.urls = {
            'back': url_for('.client_menu'),
            'quiz': quiz_url,
            'account': account_url()
        }
        return self.render()


class QuizBase(ClientPage):
    """Base class for quiz by topic and error review."""
    def get_quiz(self, *args, **kwargs):
        raise NotImplemented

    def on_request(self, *args, **kwargs):
        self.urls = {
            'back': url_for('.client_menu'),
            'image': url_for('img_file', filename='')
        }
        info = self.get_quiz(*args, **kwargs)
        return self.render(quiz=info)


class Quiz(QuizBase):
    """Quiz by topic."""
    template_name = 'ui/quiz.html'

    def get_quiz(self, topic):
        force = request.args.get('force', False)

        # TODO: what if x is not int?
        exclude = request.args.get('exclude', None)
        if exclude is not None:
            exclude = [int(x) for x in exclude.split(',')]

        self.urls['quiz'] = url_for('api.create_quiz', topic=0)[:-1]
        return app.core.getQuiz(self.quiz_type, self.uid, topic, self.lang,
                                force, exclude)


class Review(QuizBase):
    """Error review."""
    template_name = 'ui/review.html'

    def get_quiz(self):
        # TODO: what if x is not int?
        exclude = request.args.get('exclude', None)
        if exclude is not None:
            exclude = [int(x) for x in exclude.split(',')]

        self.urls['quiz'] = url_for('api.get_error_review')
        return app.core.getErrorReview(self.quiz_type, self.uid, self.lang,
                                       exclude)


class Exam(ClientPage):
    template_name = 'ui/exam.html'

    def on_request(self):
        exam_type = request.args.get('exam_type', None)
        data = app.core.createExam(self.quiz_type, self.uid, self.lang,
                                   exam_type)
        self.urls = {
            'back': url_for('.client_menu'),
            'image': url_for('img_file', filename=''),
            'exam': url_for('api.save_exam', id=0)[:-1],
            'exam_review': url_for('.client_exam_review', id=0)[:-1]
        }
        return self.render(exam=data)


class ExamReview(ClientPage):
    template_name = 'ui/exam_review.html'

    def on_request(self, id):
        info = app.core.getExamInfo(id, self.lang)
        if info['student']['id'] != access.current_user.account_id:
            abort(404)
        self.urls = {'back': url_for('.client_menu')}
        return self.render(exam=info)


### Statistics pages (accessible by clients and schools).

class ClientStatisticsPage(ClientPage):
    decorators = [access.be_user.require()]

    def render(self, **kwargs):
        if self.urls is None:
            self.urls = {}
        self.urls['account'] = account_url()
        return ClientPage.render(self, **kwargs)


# TODO: do we need guest statistics?
class Statistics(ClientStatisticsPage):
    template_name = 'ui/statistics_client.html'

    def on_request(self):
        self.urls = {'back': url_for('.client_menu')}
        stat = app.core.getUserStat(self.quiz_type, self.uid, self.lang)
        exams = app.core.getExamList(self.quiz_type, self.uid)
        return self.render(client_stat=stat, exams=exams)


class StatisticsTopic(ClientStatisticsPage):
    template_name = 'ui/statistics_client_topic.html'

    def on_request(self, topic_id):
        self.urls = {'back': url_for('.client_statistics')}
        errors = app.core.getTopicErrors(self.quiz_type, self.uid, topic_id,
                                         self.lang)
        return self.render(errors=errors)


class StatisticsExams(ClientStatisticsPage):
    template_name = 'ui/statistics_client_exams.html'

    def on_request(self, range):
        exams = app.core.getExamList(self.quiz_type, self.uid)['exams']
        total = 40  # TODO: some quizzes has different value
        range_exams = exams.get(range)
        if range_exams is None:
            range_exams = exams['week3']
            range_exams.extend(exams['week'])
            range_exams.extend(exams['current'])
        self.urls = {
            'back': url_for('.client_statistics'),
            'exam': url_for('api.get_exam_info', id=0)[:-1],
            'image': url_for('img_file', filename='')
        }
        return self.render(exams=range_exams, total=total)
