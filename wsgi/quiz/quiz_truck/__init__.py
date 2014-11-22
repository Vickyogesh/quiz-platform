"""
This package implements Quiz CQC.
"""
from flask import session, request, redirect, url_for, current_app
from flask_babelex import lazy_gettext
from flask_login import current_user
from sqlalchemy import select, and_
from ..common.base import Bundle, BaseView
from ..common import client_views, school_views, index

sublicense = {
    'title': {
        5: lazy_gettext('Truck C1 and C1E'),
        6: lazy_gettext('Truck C1 and C1E non-professional'),
        7: lazy_gettext('Truck C and CE'),
        8: lazy_gettext('Truck C and CE with C1 and C1E category'),
        9: lazy_gettext('Truck D1 and D1E'),
        10: lazy_gettext('Truck D and DE'),
        11: lazy_gettext('Truck D and DE with D1 and D1E category'),
    },
    'exam_meta': {
        5: {'max_errors': 1, 'total_time': 2000, 'num_questions': 31},
        6: {'max_errors': 2, 'total_time': 2100, 'num_questions': 32},
        7: {'max_errors': 3, 'total_time': 2200, 'num_questions': 33},
        8: {'max_errors': 4, 'total_time': 2300, 'num_questions': 34},
        9: {'max_errors': 5, 'total_time': 2400, 'num_questions': 35},
        10: {'max_errors': 6, 'total_time': 2500, 'num_questions': 36},
        11: {'max_errors': 7, 'total_time': 2600, 'num_questions': 37}
    }
}


class TruckMeta(dict):
    """Extends :class:`dict` with pseudo items.

    If one of the :attr:`TruckMeta.sub_items` is requested then lookup will be
    performed in :attr:`sublicense` dictionary depending on value
    in the session's ``sub_license``.

    It used to fit truck quiz sublicense metadata to the common quiz bundle
    structure.

    Notes:
        * This class requires request context
        * There must be ``session['sub_license']`` value.

    See Also:
        :func:`_handle_sub_license` sources.
    """
    sub_items = ('id', 'title', 'exam_meta')

    def __subitem(self, name, d=None):
        sub = session.get('sub_license')
        if name == 'id':
            return sub
        return sublicense[name][sub] if sub is not None else d

    def __getitem__(self, item):
        if item in self.sub_items:
            return self.__subitem(item)
        return dict.__getitem__(self, item)

    def get(self, k, d=None):
        if k in self.sub_items:
            return self.__subitem(item, d)
        return dict.get(self, k, d)


quiz = Bundle(__name__, TruckMeta(name='truck'))


def _handle_sub_license():
    """Handles sublicense in request.

    If ``sub`` URL query parameter is set then save it's value in the
    session and DB.

    Otherwise try to get it from DB and put on session.

    This function is used by client and school menu pages where the user
    can change sub license type.

    Note:
        ``sub`` query parameter is provided by the
        :file:`templates/quiz_truck/sublicense.html`.
    """
    user = current_user
    try:
        sub_license = int(request.args.get('sub'))
    except (ValueError, TypeError):
        sub_license = None

    user_type = 0
    if user.is_student or user.is_guest:
        user_type = 1
    elif user.is_school:
        user_type = 2

    # If sub_license is not specified in URL query then we try to get it
    # from session and then from DB.
    if sub_license is None:
        if 'sub_license' not in session:
            t = current_app.core.truck_last_sublicense

            sql = select([t.c.sublicense]).where(and_(
                t.c.user_id == user.account_id, t.c.user_type == user_type))

            res = current_app.core.engine.execute(sql).fetchone()
            if res is not None:
                sub_license = res[0]
                session['sub_license'] = sub_license
                session['quiz_id'] = sub_license
        else:
            sub_license = session['sub_license']

    # If sub_license is specified in URL query then we save it in session
    # and DB. Session one will be used by other pages and DB one will be
    # used on next login.
    else:
        t = current_app.core.truck_last_sublicense
        add = 'ON DUPLICATE KEY UPDATE sublicense=sublicense'
        sql = t.insert(append_string=add).values(user_id=user.account_id,
                                                 user_type=user_type,
                                                 sublicense=sub_license)
        current_app.core.engine.execute(sql)
        session['sub_license'] = sub_license
        session['quiz_id'] = sub_license

    # If sub_license is not found in session and DB then we redirect
    # to page with sub_license choices.
    return sub_license

# -- Common views --------------------------------------------------------------

quiz.view(client_views.ClientQuizView)
quiz.view(client_views.ClientReviewView)
quiz.view(client_views.ClientExamReviewView)
quiz.view(client_views.ClientStatisticsView)
quiz.view(client_views.ClientTopicStatisticsView)
quiz.view(client_views.ClientExamStatisticsView)
quiz.view(school_views.SchoolStatisticsView)


# -- Quiz specific views -------------------------------------------------------

# NOTE: this view has no client/school permissions check.
# Well we actually don't need it here.
@quiz.view
class SubLicense(BaseView):
    template_name = 'quiz_truck/sublicense.html'
    url_rule = '/sublicense'
    endpoint = 'sub_license'

    def render_template(self, **kwargs):
        kwargs['sublicense'] = sublicense['title']
        return BaseView.render_template(self, **kwargs)


@quiz.view
class IndexView(index.IndexView):
    @property
    def quiz_fullname(self):
        # For backward compatibility.
        # We have to send 'truck' to the Accounts Service instead of
        # truck2013.
        year = self.meta['year']
        if year == 2013:
            return self.meta['name']
        else:
            return ''.join((self.meta['name'], str(year)))


@quiz.view
class ClientMenu(client_views.ClientMenuView):
    template_name = 'quiz_truck/menu_client.html'

    def dispatch_request(self, *args, **kwargs):
        sub_license = _handle_sub_license()
        if sub_license is None:
            return redirect(url_for('.sub_license'))
        return client_views.ClientMenuView.dispatch_request(self, *args,
                                                            **kwargs)

@quiz.view
class ClientMenuQuiz(client_views.ClientTopicsView):
    template_name = 'quiz_truck/menu_topics.html'


@quiz.view
class ClientExam(client_views.ClientExamView):
    template_name = 'quiz_truck/exam.html'


@quiz.view
class SchoolMenu(school_views.SchoolMenuView):
    template_name = 'quiz_truck/menu_school.html'

    def dispatch_request(self, *args, **kwargs):
        sub_license = _handle_sub_license()
        if sub_license is None:
            return redirect(url_for('.sub_license'))
        return school_views.SchoolMenuView.dispatch_request(self)
