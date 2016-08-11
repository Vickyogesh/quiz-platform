from flask import session, request, redirect, url_for, current_app
from flask_login import current_user
from sqlalchemy import select, and_
from ..common.base import Bundle, BaseView
from ..common import client_views, school_views, index
from .data import subquiz


class RevMeta(dict):
    """Extends :class:`dict` with pseudo items.

    If one of the :attr:`.sub_items` is requested then lookup will be
    performed in :attr:`subquiz` dictionary depending on value
    in the session's ``subquiz``.

    It used to fit revisioni quiz sub quiz metadata to the common quiz bundle
    structure.

    Notes:
        * This class requires request context.
        * There must be ``session['subquiz']`` value.

    See Also:
        :func:`_handle_sub_quiz` sources.
    """
    sub_items = ('id', 'title', 'exam_meta', 'areas')

    def __subitem(self, name, d=None):
        subquiz_id = session.get('subquiz')
        if name == 'id':
            return subquiz_id
        if subquiz_id is None:
            return d
        return subquiz[subquiz_id][name]

    def __getitem__(self, item):
        if item in self.sub_items:
            return self.__subitem(item)
        return dict.__getitem__(self, item)

    def get(self, k, d=None):
        if k in self.sub_items:
            return self.__subitem(k, d)
        return dict.get(self, k, d)


quiz = Bundle(__name__, RevMeta(name='revisioni'))


def _handle_sub_quiz():
    """Handles sub quiz in request.

    If ``sub`` URL query parameter is set then save it's value in the
    session and DB.

    Otherwise try to get it from DB and put on session.

    This function is used by client and school menu pages where the user
    can change sub license type.

    Note:
        ``sub`` query parameter is provided by the
        :file:`templates/quiz_rev/subquiz.html`.
    """
    user = current_user
    try:
        sub_quiz = int(request.args.get('sub'))
    except (ValueError, TypeError):
        sub_quiz = None

    user_type = 0
    if user.is_student or user.is_guest:
        user_type = 1
    elif user.is_school:
        user_type = 2

    # If subquiz is not specified in URL query then we try to get it
    # from session and then from DB.
    if sub_quiz is None:
        if 'subquiz' not in session:
            t = current_app.core.last_subquiz

            sql = select([t.c.subquiz]).where(and_(
                t.c.quiz_type == 60,  # base quiz ID
                t.c.user_id == user.account_id, t.c.user_type == user_type))

            res = current_app.core.engine.execute(sql).fetchone()
            if res is not None:
                sub_quiz = res[0]
                session['subquiz'] = session['quiz_id'] = sub_quiz
        else:
            sub_quiz = session['subquiz']

    # If subquiz is specified in URL query then we save it in session
    # and DB. Session one will be used by other pages and DB one will be
    # used on next login.
    else:
        t = current_app.core.last_subquiz
        add = 'ON DUPLICATE KEY UPDATE subquiz=subquiz'
        sql = t.insert(append_string=add).values(quiz_type=60,
                                                 user_id=user.account_id,
                                                 user_type=user_type,
                                                 subquiz=sub_quiz)
        current_app.core.engine.execute(sql)
        session['subquiz'] = session['quiz_id'] = sub_quiz

    # If subquiz is not found in session and DB then we redirect
    # to page with subquiz choices.

    return sub_quiz


# -- Common views --------------------------------------------------------------

quiz.view(client_views.ClientQuizView)
quiz.view(client_views.ClientExamReviewView)
quiz.view(client_views.ClientStatisticsView)
quiz.view(client_views.ClientTopicStatisticsView)
quiz.view(client_views.ClientExamStatisticsView)
quiz.view(school_views.SchoolStatisticsView)


# -- Quiz specific views -------------------------------------------------------

# NOTE: this view has no client/school permissions check.
# Well we actually don't need it here.
@quiz.view
class SubQuiz(BaseView):
    template_name = 'quiz_rev/subquiz.html'
    url_rule = '/subquiz'
    endpoint = 'sub_quiz'

    def render_template(self, **kwargs):
        kwargs['subquiz'] = self.meta['title']
        return BaseView.render_template(self, **kwargs)


@quiz.view
class IndexView(index.IndexView):
    @property
    def quiz_fullname(self):
        return self.meta['name']
        # # For backward compatibility.
        # # We have to send 'truck' to the Accounts Service instead of
        # # truck2015.
        # year = self.meta['year']
        # if year == 2015:
        #     return self.meta['name']
        # else:
        #     return ''.join((self.meta['name'], str(year)))


@quiz.view
class ClientMenu(client_views.ClientMenuView):
    template_name = 'quiz_rev/menu_client.html'

    def dispatch_request(self, *args, **kwargs):
        sub_quiz = _handle_sub_quiz()
        if sub_quiz is None:
            return redirect(url_for('.sub_quiz'))
        return client_views.ClientMenuView.dispatch_request(self, *args,
                                                            **kwargs)


@quiz.view
class ClientMenuQuiz(client_views.ClientTopicsView):
    template_name = 'quiz_rev/menu_topics.html'

    # TODO: cache me
    def get_topics(self):
        t = current_app.core.topics
        sql = select([t.c.text]).where(t.c.quiz_type == self.meta['id'])
        sql = sql.order_by(t.c.id)
        res = current_app.core.engine.execute(sql)
        return [x[0] for x in res]

    def render_template(self, **kwargs):
        kwargs['topics'] = self.get_topics()
        kwargs['areas'] = self.meta['areas']
        return client_views.ClientTopicsView.render_template(self, **kwargs)


@quiz.view
class ReviewView(client_views.ClientReviewView):
    template_name = 'quiz_rev/review.html'


@quiz.view
class ClientExam(client_views.ClientExamView):
    template_name = 'quiz_rev/exam.html'


@quiz.view
class SchoolMenu(school_views.SchoolMenuView):
    template_name = 'quiz_rev/menu_school.html'

    def dispatch_request(self, *args, **kwargs):
        sub_quiz = _handle_sub_quiz()
        if sub_quiz is None:
            return redirect(url_for('.sub_quiz'))
        return school_views.SchoolMenuView.dispatch_request(self)
