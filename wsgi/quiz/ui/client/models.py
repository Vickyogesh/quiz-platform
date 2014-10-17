############################################################
# Models for pages which exists in a common quiz.
############################################################
from flask import url_for, request, session, abort
from ... import app, access
from ...api import get_user_id
from ...core.exceptions import QuizCoreError
from ..babel import gettext
from ..page import PageModel
from ..util import account_url


### Menu

class MenuModel(PageModel):
    """Common menu model.

     It adds account url to template.
     Subclass may only set :attr:`template` value.
    """
    def on_request(self, *args, **kwargs):
        self.page.urls = {'account': account_url()}
        return PageModel.on_request(self, *args, **kwargs)


class QuizMenuModel(PageModel):
    """Common quiz menu model.

    It adds some urls to template.
     Subclass may only set :attr:`template` value.
    """
    def on_request(self, *args, **kwargs):
        self.page.urls = {
            'back': url_for('.client_menu'),
            'quiz': url_for('.client_quiz', topic=0)[:-1],
            'account': account_url()
        }
        return PageModel.on_request(self, *args, **kwargs)


### Quiz/Review

class BaseQuizModel(PageModel):
    """Base class for quiz and review models.

    Provides common routines for both of them.
    Adds some urls to template.
    """
    def get_quiz(self, *args, **kwargs):
        """Return questions for quiz/review.

        Must be overridden in subclass.
        """
        raise NotImplemented

    def on_request(self, *args, **kwargs):
        self.page.urls = {
            'back': url_for('.client_menu'),
            'image': url_for('img_file', filename='')
        }
        info = self.get_quiz(*args, **kwargs)
        return self.page.render(quiz=info)


class QuizModel(BaseQuizModel):
    """Quiz model.

    Implements common quiz and may be used for each quiz type without changes.
    """
    template = 'ui/common_quiz.html'

    def get_quiz(self, topic):
        force = request.args.get('force', False)

        # TODO: what if x is not int?
        exclude = request.args.get('exclude', None)
        if exclude is not None:
            exclude = [int(x) for x in exclude.split(',')]

        self.page.urls['quiz'] = url_for('api.create_quiz', topic=0)[:-1]
        return app.core.getQuiz(self.page.quiz_id, self.page.uid, topic,
                                self.page.lang, force, exclude)


class ReviewModel(BaseQuizModel):
    """Error review.

    Implements common review and may be used for each quiz type without changes.
    """
    template = 'ui/common_review.html'

    def get_quiz(self):
        # TODO: what if x is not int?
        exclude = request.args.get('exclude', None)
        if exclude is not None:
            exclude = [int(x) for x in exclude.split(',')]

        self.page.urls['quiz'] = url_for('api.get_error_review')
        return app.core.getErrorReview(self.page.quiz_id, self.page.uid,
                                       self.page.lang, exclude)


### Exam/Exam review

class ExamModel(PageModel):
    """Base exam page model.

    It adds some urls and facebook data to template.
    Subclass must provide at least :attr:`exam_meta` and :attr:`template`.
    """
    exam_meta = None

    def on_request(self, *args, **kwargs):
        exam_type = request.args.get('exam_type', None)
        data = app.core.createExam(self.page.quiz_id, self.page.uid,
                                   self.page.lang, exam_type)
        self.page.urls = {
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
        return self.page.render(exam=data, fb_data=fb_data,
                                exam_meta=self.exam_meta)


class ExamReviewModel(PageModel):
    """Exam review page model.

    Implements common exam answers review
    and may be used for each quiz type without changes.
    """
    template = 'ui/common_exam_review.html'

    def on_request(self, id):
        info = app.core.getExamInfo(id, self.page.lang)
        if info['student']['id'] != access.current_user.account_id:
            abort(404)
        self.page.urls = {'back': url_for('.client_menu')}
        return self.page.render(exam=info)


### Statistics

# TODO: add docs about 'force_name'.
class StatisticsBaseModel(PageModel):
    """Base class for all client statistics page models.

    It provides access check method and handles 'name' url parameter.
    """
    def check(self, user_id, user_school_id):
        # If we are school then requested client must have the same
        # parent school ID.
        if access.current_user.is_school:
            if self.page.uid != user_school_id:
                abort(404)
        # If we are client then requested client must have the same ID.
        elif self.page.uid != user_id:
            abort(404)

    def render(self, *args, **kwargs):
        force_name = request.args.get('name', session.get('force_name'))
        if force_name is not None:
            kwargs['force_name'] = force_name
            session['force_name'] = force_name
        self.page.urls['account'] = account_url()
        return self.page.render(*args, **kwargs)


class StatisticsModel(StatisticsBaseModel):
    """Client statistics page model.

    May be used for each quiz type without changes.
    """
    template = 'ui/statistics_client.html'
    exam_meta = None

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
            stat = app.core.getUserStat(self.page.quiz_id, user_id,
                                        self.page.lang)
        except QuizCoreError:
            stat = None
            exams = None
        else:
            self.check(user_id, stat['student']['school_id'])
            exams = app.core.getExamList(self.page.quiz_id, user_id)

        self.page.urls = {'back': self.get_back_url()}
        return self.render(client_stat=stat, exams=exams, uid=uid,
                           exam_meta=self.exam_meta)


class StatisticsTopicModel(StatisticsBaseModel):
    """Client topics statistics page model.

    May be used for each quiz type without changes.
    """
    template = 'ui/statistics_client_topic.html'

    def on_request(self, uid, topic_id):
        user_id = get_user_id(uid)
        self.page.urls = {'back': url_for('.client_statistics', uid=uid)}
        errors = app.core.getTopicErrors(self.page.quiz_id, user_id, topic_id,
                                         self.page.lang)

        self.check(user_id, errors['student']['school_id'])
        return self.render(errors=errors)


class StatisticsExamsModel(StatisticsBaseModel):
    """Client exams statistics page model.

    May be used for each quiz type without changes.
    """
    template = 'ui/statistics_client_exams.html'
    num_exam_questions = 40

    def on_request(self, uid, range):
        user_id = get_user_id(uid)
        info = app.core.getExamList(self.page.quiz_id, user_id)
        exams = info['exams']

        self.check(user_id, info['student']['school_id'])

        range_exams = exams.get(range)
        if range_exams is None:
            range_exams = exams['week3']
            range_exams.extend(exams['week'])
            range_exams.extend(exams['current'])
        self.page.urls = {
            'back': url_for('.client_statistics', uid=uid),
            'exam': url_for('api.get_exam_info', id=0)[:-1],
            'image': url_for('img_file', filename='')
        }
        return self.render(exams=range_exams, total=self.num_exam_questions)

