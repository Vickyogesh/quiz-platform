"""
This module provides common client related quiz views.
"""
from flask import redirect, url_for, request, current_app, abort, session
from flask_login import current_user
from flask_babelex import gettext
from .base import BaseView, account_url
from .. import access
from ..api import get_user_id
from ..core.exceptions import QuizCoreError


class ClientView(BaseView):
    """Base client page view.

    It adds to the :class:`BaseView` client permission check and account URL
    for template.
    """
    decorators = [access.be_client_or_guest.require()]

    @staticmethod
    def account_url():
        """Account page URL.

        See Also:
            :func:`.base.account_url`.
        """
        return account_url()

    def page_urls(self):
        return {'account': ClientView.account_url()}


class ClientFullscreenView(ClientView):
    """Common page with fullscreen wrapper for all client's pages.
    It fallbacks to normal pages for mobile browsers.
    """
    template_name = 'client_fullscreen_wrapper.html'
    url_rule = '/fmenu'
    endpoint = 'client_fullscreen'

    @classmethod
    def is_mobile(cls):
        p = request.user_agent.platform

        if p == 'android' or p == 'iphone' or p == 'ipad' or \
           (p == 'windows' and 'Phone' in request.user_agent.string):
            return True
        return False

    def dispatch_request(self, *args, **kwargs):
        if ClientFullscreenView.is_mobile():
            return redirect(url_for('.client_menu'))
        else:
            return self.render_template()


# -- Quiz & Review views -------------------------------------------------------

class ClientTopicsView(ClientView):
    """Common view for the quiz topics page.

    It adds to the template common URLs:

    * back - Client menu page URL.
    * quiz - Quiz by topic base URL.
    * account - Account page URL.
    """
    endpoint = 'client_menu_quiz'

    def page_urls(self):
        return {
            'back': url_for('.client_menu'),
            'quiz': url_for('.client_quiz', topic=0)[:-1],
            'account': ClientView.account_url()
        }


class QuizViewBase(ClientView):
    """Base class for Quiz & Review views.

    It adds common URLs to the template and supposed to be subclassed.
    In a subclass you reimplement :meth:`QuizViewBase.get_quiz` to provide
    quiz or review questions for the template.
    """
    def page_urls(self):
        return {
            'back': url_for('.client_menu'),
            'image': url_for('img_file', filename='')
        }

    def dispatch_request(self, *args, **kwargs):
        """Render template on request."""
        return self.render_template(quiz=self.get_quiz(*args, **kwargs))

    def get_quiz(self, *args, **kwargs):
        """Return questions for quiz/review.

        Must be overridden in subclass.
        """
        raise NotImplemented


class ClientQuizView(QuizViewBase):
    """Common quiz view.

    It adds extra template URL - ``quiz`` and implements common
    quiz building algo in the :meth:`~QuizViewBase.get_quiz`.

    May be used without changes for various quiz types.
    """
    template_name = 'common_quiz.html'
    url_rule = '/quiz/<int:topic>'
    endpoint = 'client_quiz'

    def page_urls(self):
        urls = QuizViewBase.page_urls(self)
        urls['quiz'] = url_for('api.create_quiz', topic=0)[:-1]
        return urls

    def get_quiz(self, topic):
        force = request.args.get('force', False)
        uid = current_user.account_id

        # TODO: what if x is not int?
        exclude = request.args.get('exclude', None)
        if exclude is not None:
            exclude = [int(x) for x in exclude.split(',')]

        return current_app.core.getQuiz(self.meta['id'], uid, topic,
                                        self.request_lang, force, exclude)


class ClientReviewView(QuizViewBase):
    """Common quiz review view.

    It adds extra template URL and implements common review algo.

    May be used without changes for various quiz types.
    """
    template_name = 'common_review.html'
    endpoint = 'client_review'

    def page_urls(self):
        urls = QuizViewBase.page_urls(self)
        urls['quiz'] = url_for('api.get_error_review')
        return urls

    def get_quiz(self):
        uid = current_user.account_id

        # TODO: what if x is not int?
        exclude = request.args.get('exclude', None)
        if exclude is not None:
            exclude = [int(x) for x in exclude.split(',')]

        return current_app.core.getErrorReview(self.meta['id'], uid,
                                               self.request_lang, exclude)


# -- Exam views ----------------------------------------------------------------

class ClientExamView(ClientView):
    """Common exam view.

    It supposed to be subclassed and set template name.
    """
    endpoint = 'client_exam'
    url_rule = '/exam'

    def page_urls(self):
        urls = ClientView.page_urls(self)
        urls['quiz'] = url_for('api.get_error_review')
        urls['back'] = url_for('.client_menu')
        urls['image'] = url_for('img_file', filename='')
        urls['exam'] = url_for('api.save_exam', id=0)[:-1]
        urls['exam_review'] = url_for('.client_exam_review', id=0)[:-1]
        return urls

    def dispatch_request(self):
        exam_type = request.args.get('exam_type', None)
        uid = current_user.account_id
        data = current_app.core.createExam(self.meta['id'], uid,
                                           self.request_lang, exam_type)
        if 'fb_id' in current_user.account:
            fb_data = {
                'id': current_user.account['fb_id'],
                'text': gettext('Number of errors in exam: %%(num)s'),
                'description': 'Quiz Patente',
                'school_title': session.get('extra_school_name'),
                'school_link': session.get('extra_school_url'),
                'school_logo_url': session.get('extra_school_logo_url')
            }
            fb_data = dict((k, v) for k, v in fb_data.iteritems() if v)
        else:
            fb_data = None
        return self.render_template(exam=data, fb_data=fb_data)


class ClientExamReviewView(ClientView):
    """Common exam review view.

    May be used without changes for various quiz types.
    """
    template_name = 'common_exam_review.html'
    endpoint = 'client_exam_review'
    url_rule = '/exam_review/<int:id>'

    def page_urls(self):
        urls = ClientView.page_urls(self)
        urls['back'] = url_for('.client_menu')
        return urls

    def dispatch_request(self, id):
        info = current_app.core.getExamInfo(id, self.request_lang)
        if info['student']['id'] != current_user.account_id:
            abort(404)
        return self.render_template(exam=info)


# -- Statistics views ----------------------------------------------------------

class ClientStatisticsBase(ClientView):
    """Base class for the client statistics views.

    It limits access to the page only by clients excluding guest users and
    handles ``name`` URL query parameter.

    May be used without changes for various quiz types.
    """
    decorators = [access.be_user.require()]

    @staticmethod
    def check(user_id, user_school_id):
        """Check if current user can access to the statistics.

        * If user is a school then requested statistics must belongs to the
          school's client.
        * If user is a school's client then requested statistics must belongs
          to him.
        * In other cases HTTP 404 will be raised.
        """
        # If we are school then requested client must have the same
        # parent school ID.
        if current_user.is_school:
            if current_user.account_id != user_school_id:
                abort(404)
        # If we are client then requested client must have the same ID.
        elif current_user.account_id != user_id:
            abort(404)

    def page_urls(self):
        urls = ClientView.page_urls(self)
        urls['account'] = account_url()
        return urls

    def render_template(self, **kwargs):
        force_name = request.args.get('name', session.get('force_name'))
        if force_name is not None:
            session['force_name'] = force_name
            kwargs['force_name'] = force_name
        return ClientView.render_template(self, **kwargs)


class ClientStatisticsView(ClientStatisticsBase):
    """Common client statistics view.

    Provides the following features:

    * Back url:
      This is a workaround to correctly redirect to previous page.
      School can view client statistics from two locations:
      menu page and school statistics page,
      and to determine which page was before the client's page we
      save URL in session.
      School's statistics passes it query; school menu page doesn't set
      back URL at all. Client's stat page (this page) saves it
      in session. And later can extract it.
      For more info see :meth:`ClientStatistics.page_urls` sources.

    May be used without changes for various quiz types.
    """
    template_name = 'common_statistics_client.html'
    endpoint = 'client_statistics'
    url_rule = (
        ('/statistics', {'defaults': {'uid': 'me'}}),
        ('/statistics/<uid:uid>',),
    )

    def page_urls(self):
        urls = ClientStatisticsBase.page_urls(self)

        # See class docs.
        back_url = request.args.get('back', session.get('back_url'))
        if back_url is None:
            if access.current_user.is_school:
                back_url = url_for('.school_menu')
            else:
                back_url = url_for('.client_menu')
        session['back_url'] = back_url

        urls['back'] = back_url
        return urls

    def dispatch_request(self, uid):
        user_id = get_user_id(uid)
        try:
            stat = current_app.core.getUserStat(self.meta['id'], user_id,
                                                self.request_lang)
        except QuizCoreError:
            stat = None
            exams = None
        else:
            self.check(user_id, stat['student']['school_id'])
            exams = current_app.core.getExamList(self.meta['id'], user_id)
        return self.render_template(client_stat=stat, exams=exams, uid=uid)


class ClientTopicStatisticsView(ClientStatisticsBase):
    """Common client topic statistics view.

    It provides back URL depending on request URL and implements
    common topics info algo.

    May be used without changes for various quiz types.
    """
    template_name = 'common_statistics_client_topic.html'
    endpoint = 'client_statistics_topic'
    url_rule = '/statistics/<uid:uid>/topic/<int:topic_id>'

    def __init__(self):
        # Used to create back url depending on request.
        self._uid = None

    def page_urls(self):
        urls = ClientStatisticsBase.page_urls(self)
        urls['back'] = url_for('.client_statistics', uid=self._uid)
        return urls

    def dispatch_request(self, uid, topic_id):
        user_id = get_user_id(uid)
        self._uid = uid
        errors = current_app.core.getTopicErrors(self.meta['id'], user_id,
                                                 topic_id, self.request_lang)

        self.check(user_id, errors['student']['school_id'])
        return self.render_template(errors=errors, uid=uid)


class ClientExamStatisticsView(ClientStatisticsBase):
    """Common exam statistics view.

    It provides URLs for the template and implements common exam info logic.

    May be used without changes for various quiz types.
    """
    template_name = 'common_statistics_client_exams.html'
    endpoint = 'client_statistics_exams'
    url_rule = '/statistics/<uid:uid>/exams/<range>'

    def __init__(self):
        # Used to create back url depending on request.
        self._uid = None

    def page_urls(self):
        urls = ClientStatisticsBase.page_urls(self)
        urls['back'] = url_for('.client_statistics', uid=self._uid)
        urls['exam'] = url_for('api.get_exam_info', id=0)[:-1]
        urls['image'] = url_for('img_file', filename='')
        return urls

    def dispatch_request(self, uid, range):
        user_id = get_user_id(uid)
        self._uid = uid
        info = current_app.core.getExamList(self.meta['id'], user_id)
        exams = info['exams']

        self.check(user_id, info['student']['school_id'])

        range_exams = exams.get(range)
        if range_exams is None:
            range_exams = exams['week3']
            range_exams.extend(exams['week'])
            range_exams.extend(exams['current'])
        return self.render_template(exams=range_exams)

