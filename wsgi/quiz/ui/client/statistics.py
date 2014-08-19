from flask import url_for, session, request, abort
from ... import access, app
from ...api import get_user_id
from ...core.exceptions import QuizCoreError
from ..page import PageModel, ClientPage
from ..util import account_url


############################################################
# Models
############################################################

class StatisticsBaseModel(PageModel):
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
    template = 'ui/statistics_client.html'

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
        return self.render(client_stat=stat, exams=exams, uid=uid)


class StatisticsTopicModel(StatisticsBaseModel):
    template = 'ui/statistics_client_topic.html'

    def on_request(self, uid, topic_id):
        user_id = get_user_id(uid)
        self.page.urls = {'back': url_for('.client_statistics', uid=uid)}
        errors = app.core.getTopicErrors(self.page.quiz_id, user_id, topic_id,
                                         self.page.lang)

        self.check(user_id, errors['student']['school_id'])
        return self.render(errors=errors)


class StatisticsExamsModel(StatisticsBaseModel):
    template = 'ui/statistics_client_exams.html'

    def on_request(self, uid, range):
        user_id = get_user_id(uid)
        info = app.core.getExamList(self.page.quiz_id, user_id)
        exams = info['exams']

        self.check(user_id, info['student']['school_id'])

        total = 40  # TODO: some quizzes has different value
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
        return self.render(exams=range_exams, total=total)


############################################################
# Views
############################################################

class Statistics(ClientPage):
    models = {'': StatisticsModel}


class StatisticsTopic(ClientPage):
    models = {'': StatisticsTopicModel}


class StatisticsExams(ClientPage):
    models = {'': StatisticsExamsModel}
