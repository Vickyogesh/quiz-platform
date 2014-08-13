# coding=utf-8
from flask import url_for, request, abort, session
from .page import Page
from .util import account_url
from .. import access, app
from ..api import get_user_id
from ..core.exceptions import QuizCoreError
from .babel import gettext, lazy_gettext


def register_urls_for(bp):
    bp.route('/c/menu')(Menu.get_view())
    bp.route('/c/menu/quiz')(MenuQuiz.get_view())
    bp.route('/c/quiz/<int:topic>')(Quiz.get_view())
    bp.route('/c/review')(Review.get_view())
    bp.route('/c/exam')(Exam.get_view())
    bp.route('/c/exam_review/<int:id>')(ExamReview.get_view())

    view = Statistics.get_view()
    bp.route('/c/statistics', defaults={'uid': 'me'})(view)
    bp.route('/c/statistics/<uid:uid>')(view)
    bp.route('/c/statistics/<uid:uid>/topic/<int:topic_id>')(
        StatisticsTopic.get_view())
    bp.route('/c/statistics/<uid:uid>/exams/<range>')(
        StatisticsExams.get_view())


### Client only pages

class ClientPage(Page):
    decorators = [access.be_client_or_guest.require()]
    endpoint_prefix = 'client'


class Menu(ClientPage):
    default_template = 'ui/menu_client.html'

    def on_request(self):
        self.urls = {'account': account_url()}
        return self.render()


class MenuQuiz(ClientPage):
    default_template = 'ui/menu_quiz.html'
    templates = {
        'scooter': 'ui/scooter/menu_quiz.html'
    }

    scooter_topics = [
        (lazy_gettext(u'Segnali di pericolo'),
         lazy_gettext(u'Segnali di divieto, segnali di obbligo, segnali di precedenza')
        ),
        (lazy_gettext(u'Pannelli integrativi, segnali di indicazione, segnali luminosi, segnali orizzontali'),
         lazy_gettext(u'Norme sulla precedenza')
        ),
        (lazy_gettext(u'Velocità, distanza di sicurezza, sorpasso, svolta, cambio di corsia, cambio di direzione'),
         lazy_gettext(u'Fermata, sosta, definizioni stradali')
        ),
        (lazy_gettext(u'Cause di incidenti, assicurazione'),
         lazy_gettext(u'Elementi del ciclomotore e loro uso, casco')
        ),
        (lazy_gettext(u'Comportamenti alla guida del ciclomotore'),
         lazy_gettext(u'Educazione alla legalità')
        )
    ]

    def scooter_template_params(self):
        return {'topics': self.scooter_topics}

    def on_request(self):
        self.urls = {
            'back': url_for('.client_menu'),
            'quiz': url_for('.client_quiz', topic=0)[:-1],
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
    default_template = 'ui/quiz.html'

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
    default_template = 'ui/review.html'

    def get_quiz(self):
        # TODO: what if x is not int?
        exclude = request.args.get('exclude', None)
        if exclude is not None:
            exclude = [int(x) for x in exclude.split(',')]

        self.urls['quiz'] = url_for('api.get_error_review')
        return app.core.getErrorReview(self.quiz_type, self.uid, self.lang,
                                       exclude)


class Exam(ClientPage):
    default_template = 'ui/exam.html'
    templates = {
        'scooter': 'ui/scooter/exam.html'
    }

    def scooter_template_params(self):
        return {
            'exam_meta': {'max_errors': 3, 'total_time': 1500}
        }

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

        if 'fb_id' in access.current_user.account:
            fb_data = {
                'id': access.current_user.account['fb_id'],
                'text': gettext('Number of errors in exam: %%(num)s'),
                'description': 'Quiz Patente',
                'school_title': session.get('extra_school_name'),
                'school_link': session.get('extra_school_url'),
                'school_logo_url': session.get('extra_school_logo_url')
            }
            fb_data = dict((k, v) for k, v in fb_data.iteritems() if v)
        else:
            fb_data = None
        default_meta = {'max_errors': 4, 'total_time': 1800}
        return self.render(exam=data, fb_data=fb_data, exam_meta=default_meta)


class ExamReview(ClientPage):
    default_template = 'ui/exam_review.html'

    def on_request(self, id):
        info = app.core.getExamInfo(id, self.lang)
        if info['student']['id'] != access.current_user.account_id:
            abort(404)
        self.urls = {'back': url_for('.client_menu')}
        return self.render(exam=info)


### Statistics pages (accessible by clients and schools).

class ClientStatisticsPage(ClientPage):
    decorators = [access.be_user.require()]

    def check(self, user_id, user_school_id):
        # If we are school then requested client must have the same
        # parent school ID.
        if access.current_user.is_school:
            if self.uid != user_school_id:
                abort(404)
        # If we are client then requested client must have the same ID.
        elif self.uid != user_id:
            abort(404)

    def render(self, **kwargs):
        if self.urls is None:
            self.urls = {}
        self.urls['account'] = account_url()
        force_name = request.args.get('name', session.get('force_name'))
        if force_name is not None:
            kwargs['force_name'] = force_name
            session['force_name'] = force_name
        return ClientPage.render(self, **kwargs)


# TODO: do we need guest statistics?
class Statistics(ClientStatisticsPage):
    default_template = 'ui/statistics_client.html'

    # Back URL:
    # This is a workaround to correctly redirect to previous page.
    # School can view client statistics from two locations:
    # menu page and school statistics page,
    # and to determine which page was before the client's page we
    # save URL in session.
    # School's statistics passes it query; school menu page doesn't set
    # back URL at all. Client's stat page (this page) saves it
    # in session. And later can extract it.
    def get_back_url(self):
        back_url = request.args.get('back', session.get('back_url'))
        if back_url is None:
            if access.current_user.is_school:
                back_url = url_for('.school_menu')
            else:
                back_url = url_for('.client_menu')
        session['back_url'] = back_url
        return back_url

    def on_request(self, uid):
        user_id = get_user_id(uid)
        try:
            stat = app.core.getUserStat(self.quiz_type, user_id, self.lang)
        except QuizCoreError:
            stat = None
            exams = None
        else:
            self.check(user_id, stat['student']['school_id'])
            exams = app.core.getExamList(self.quiz_type, user_id)

        self.urls = {'back': self.get_back_url()}
        return self.render(client_stat=stat, exams=exams, uid=uid)


class StatisticsTopic(ClientStatisticsPage):
    default_template = 'ui/statistics_client_topic.html'

    def on_request(self, uid, topic_id):
        user_id = get_user_id(uid)
        self.urls = {'back': url_for('.client_statistics', uid=uid)}
        errors = app.core.getTopicErrors(self.quiz_type, user_id, topic_id,
                                         self.lang)

        self.check(user_id, errors['student']['school_id'])

        return self.render(errors=errors)


class StatisticsExams(ClientStatisticsPage):
    default_template = 'ui/statistics_client_exams.html'

    def on_request(self, uid, range):
        user_id = get_user_id(uid)
        info = app.core.getExamList(self.quiz_type, user_id)
        exams = info['exams']

        self.check(user_id, info['student']['school_id'])

        total = 40  # TODO: some quizzes has different value
        range_exams = exams.get(range)
        if range_exams is None:
            range_exams = exams['week3']
            range_exams.extend(exams['week'])
            range_exams.extend(exams['current'])
        self.urls = {
            'back': url_for('.client_statistics', uid=uid),
            'exam': url_for('api.get_exam_info', id=0)[:-1],
            'image': url_for('img_file', filename='')
        }
        return self.render(exams=range_exams, total=total)
