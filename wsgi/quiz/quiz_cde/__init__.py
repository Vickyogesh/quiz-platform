# coding=utf-8
"""
This package implements Quiz CQC.
"""
from flask import session, request, redirect, url_for, current_app
from flask_babelex import lazy_gettext, gettext
from flask_login import current_user
from sqlalchemy import select, and_
from ..common.base import Bundle, BaseView
from ..common import client_views, school_views, index

sublicense = {
    'title': {
        5: lazy_gettext('Licenses categories C1 - C1E'),
        6: lazy_gettext('Licenses categories C1 - C1E code Union 97'),
        7: lazy_gettext('Licenses categories C - CE'),
        8: lazy_gettext('Licenses categories C - CE formerly C1'),
        9: lazy_gettext('Licenses categories D1 - D1E'),
        10: lazy_gettext('Licenses categories D - DE'),
        11: lazy_gettext('Licenses categories D - DE formerly D1'),
    },
    'exam_meta': {
        5: {
            'max_errors': 2,
            'total_time': 1200,
            'num_questions': 20,
            'questions_per_chapter': [2, 3, 3, 1, 3, 1, 3, 1, 1, 2]
        },
        6: {
            'max_errors': 1,
            'total_time': 1200,
            'num_questions': 10,
            'questions_per_chapter': [2, 1, 3, 1, 1, 2]

        },
        7: {
            'max_errors': 4,
            'total_time': 2400,
            'num_questions': 40,
            'questions_per_chapter': [2, 3, 4, 1, 2, 1, 3, 1, 1, 2, 5, 1, 4, 3,
                                      3, 3, 1]

        },
        8: {
            'max_errors': 2,
            'total_time': 1200,
            'num_questions': 20,
            'questions_per_chapter': [5, 1, 4, 3, 3, 3, 1]

        },
        9: {
            'max_errors': 2,
            'total_time': 1200,
            'num_questions': 20,
            'questions_per_chapter': [2, 3, 2, 1, 2, 2, 3, 1, 2, 2]

        },
        10: {
            'max_errors': 4,
            'total_time': 2400,
            'num_questions': 40,
            'questions_per_chapter': [2, 3, 3, 1, 3, 2, 3, 1, 2, 2, 5, 1, 4, 2,
                                      3, 3]

        },
        11: {
            'max_errors': 2,
            'total_time': 1200,
            'num_questions': 20,
            'questions_per_chapter': [5, 2, 4, 3, 3, 3]

        }
    }
}

# NOTE: areas list is build with help of misc/csvtosqlite.py

# NOTE: few areas has 'cls' item - custom class for the html tag.
# QuizMenuView supports it, see QuizAreaPageView.render()
# in static/js/quiz-menu.js.

areas = {
    5: [
        {
            'text': u'Normativa sociale',
            'chapters': [[1], [2]],
            'chapter_numbers': [1, 2]
        },
        {
            'text': u'Disposizioni per il trasporto nazionale e internazionale',
            'chapters': [[3, 4, 5, 6], [7]],
            'chapter_numbers': [3, 4]
        },
        {
            'text': u'Incidenti ed emergenza',
            'chapters': [[8, 9, 10], [11]],
            'chapter_numbers': [5, 6]
        },
        {
            'text': u'Massa, dimensione dei veicoli e limitazione del campo visivo',
            'chapters': [[12, 13, 14, 15], [16]],
            'chapter_numbers': [7, 8]
        },
        {
            'text': u'Carico, aggancio e vari tipi di veicoli pesanti',
            'chapters': [[17, 18], [19, 20, 21]],
            'chapter_numbers': [9, 10]
        }
    ],
    6: [
        {
            'text': u'Incidenti ed emergenza',
            'chapters': [[1, 2, 3], [4]],
            'chapter_numbers': [5, 6],
            'cls': 'area3'
        },
        {
            'text': u'Massa, dimensione dei veicoli e limitazione del campo visivo',
            'chapters': [[5, 6, 7, 8], [9]],
            'chapter_numbers': [7, 8],
            'cls': 'area4'
        },
        {
            'text': u'Carico, aggancio e vari tipi di veicoli pesanti',
            'chapters': [[10, 11], [12, 13, 14]],
            'chapter_numbers': [9, 10],
            'cls': 'area5'
        }
    ],
    7: [
        {
            'text': u'Normativa sociale',
            'chapters': [[1], [2]],
            'chapter_numbers': [1, 2]
        },
        {
            'text': u'Disposizioni per il trasporto nazionale e internazionale',
            'chapters': [[3, 4, 5, 6], [7]],
            'chapter_numbers': [3, 4]
        },
        {
            'text': u'Incidenti ed emergenza',
            'chapters': [[8, 9, 10], [11]],
            'chapter_numbers': [5, 6]
        },
        {
            'text': u'Massa, dimensione dei veicoli e limitazione del campo visivo',
            'chapters': [[12, 13, 14, 15], [16]],
            'chapter_numbers': [7, 8]
        },
        {
            'text': u'Carico, aggancio e vari tipi di veicoli pesanti',
            'chapters': [[17, 18], [19, 20, 21]],
            'chapter_numbers': [9, 10]
        },
        {
            'text': u'Tecnica e funzionamento dei veicoli',
            'chapters': [[22, 23, 24, 25, 26], [27, 28], [29, 30, 31], [32]],
            'chapter_numbers': [11, 12, 13, 14]
        },
        {
            'text': u'Manutenzione e guasti',
            'chapters': [[33, 34, 35, 36], [37, 38, 39, 40]],
            'chapter_numbers': [15, 16]
        },
        {
            'text': u'Responsabilità del conducente nel trasporto di merci',
            'chapters': [[41]],
            'chapter_numbers': [17]
        }
    ],
    8: [
        {
            'text': u'Tecnica e funzionamento dei veicoli',
            'chapters': [[1, 2, 3, 4, 5], [6, 7], [8, 9, 10], [11]],
            'chapter_numbers': [11, 12, 13, 14],
            'cls': 'area6'
        },
        {
            'text': u'Manutenzione e guasti',
            'chapters': [[12, 13, 14, 15], [16, 17, 18, 19]],
            'chapter_numbers': [15, 16],
            'cls': 'area7'
        },
        {
            'text': u'Responsabilità del conducente nel trasporto di merci',
            'chapters': [[20]],
            'chapter_numbers': [17],
            'cls': 'area8'
        }
    ],
    9: [
        {
            'text': u'Normativa sociale',
            'chapters': [[1], [2]],
            'chapter_numbers': [1, 2]
        },
        {
            'text': u'Disposizioni per il trasporto nazionale e internazionale',
            'chapters': [[3], [4]],
            'chapter_numbers': [3, 4]
        },
        {
            'text': u'Incidenti ed emergenza',
            'chapters': [[5, 6, 7], [8]],
            'chapter_numbers': [5, 6]
        },
        {
            'text': u'Massa, dimensione dei veicoli e limitazione del campo visivo',
            'chapters': [[9, 10, 11, 12], [13]],
            'chapter_numbers': [7, 8]
        },
        {
            'text': u'Carico, aggancio e vari tipi di veicoli pesanti',
            'chapters': [[14, 15, 16], [17, 18]],
            'chapter_numbers': [9, 10]
        }
    ],
    10: [
        {
            'text': u'Normativa sociale',
            'chapters': [[1], [2]],
            'chapter_numbers': [1, 2]
        },
        {
            'text': u'Disposizioni per il trasporto nazionale e internazionale',
            'chapters': [[3], [4]],
            'chapter_numbers': [3, 4]
        },
        {
            'text': u'Incidenti ed emergenza',
            'chapters': [[5, 6, 7], [8]],
            'chapter_numbers': [5, 6]
        },
        {
            'text': u'Massa, dimensione dei veicoli e limitazione del campo visivo',
            'chapters': [[9, 10, 11, 12], [13]],
            'chapter_numbers': [7, 8]
        },
        {
            'text': u'Carico, aggancio e vari tipi di veicoli pesanti',
            'chapters': [[14, 15, 16], [17, 18]],
            'chapter_numbers': [9, 10]
        },
        {
            'text': u'Tecnica e funzionamento dei veicoli',
            'chapters': [[19, 20, 21, 22, 23], [24, 25], [26, 27, 28], [29]],
            'chapter_numbers': [11, 12, 13, 14]
        },
        {
            'text': u'Manutenzione e guasti',
            'chapters': [[30, 31, 32, 33], [34, 35, 36, 37]],
            'chapter_numbers': [15, 16]
        }
    ],
    11: [
        {
            'text': u'Tecnica e funzionamento dei veicoli',
            'chapters': [[1, 2, 3, 4, 5], [6, 7], [8, 9, 10], [11]],
            'chapter_numbers': [11, 12, 13, 14],
            'cls': 'area6'
        },
        {
            'text': u'Manutenzione e guasti',
            'chapters': [[12, 13, 14, 15], [16, 17, 18, 19]],
            'chapter_numbers': [15, 16],
            'cls': 'area7'
        }
    ]
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
        elif sub is None and name == 'title':
            return gettext('C D E')
        return sublicense[name][sub] if sub is not None else d

    def __getitem__(self, item):
        if item in self.sub_items:
            return self.__subitem(item)
        return dict.__getitem__(self, item)

    def get(self, k, d=None):
        if k in self.sub_items:
            return self.__subitem(k, d)
        return dict.get(self, k, d)


quiz = Bundle(__name__, TruckMeta(name='cde'))


def _handle_sub_license():
    """Handles sublicense in request.

    If ``sub`` URL query parameter is set then save it's value in the
    session and DB.

    Otherwise try to get it from DB and put on session.

    This function is used by client and school menu pages where the user
    can change sub license type.

    Note:
        ``sub`` query parameter is provided by the
        :file:`templates/quiz_cde/sublicense.html`.
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
    template_name = 'quiz_cde/sublicense.html'
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
        # truck2015.
        year = self.meta['year']
        if year == 2015:
            return self.meta['name']
        else:
            return ''.join((self.meta['name'], str(year)))


@quiz.view
class ClientMenu(client_views.ClientMenuView):
    template_name = 'quiz_cde/menu_client.html'

    def dispatch_request(self, *args, **kwargs):
        sub_license = _handle_sub_license()
        if sub_license is None:
            return redirect(url_for('.sub_license'))
        return client_views.ClientMenuView.dispatch_request(self, *args,
                                                            **kwargs)

@quiz.view
class ClientMenuQuiz(client_views.ClientTopicsView):
    template_name = 'quiz_cde/menu_topics.html'

    # TODO: cache me
    def get_topics(self):
        t = current_app.core.topics
        sql = select([t.c.text]).where(t.c.quiz_type == self.meta['id'])
        sql = sql.order_by(t.c.id)
        res = current_app.core.engine.execute(sql)
        return [x[0] for x in res]

    def render_template(self, **kwargs):
        kwargs['topics'] = self.get_topics()
        kwargs['areas'] = areas[self.meta['id']]
        return client_views.ClientTopicsView.render_template(self, **kwargs)


@quiz.view
class ReviewView(client_views.ClientReviewView):
    template_name = 'quiz_cde/review.html'


@quiz.view
class ClientExam(client_views.ClientExamView):
    template_name = 'quiz_cde/exam.html'


@quiz.view
class SchoolMenu(school_views.SchoolMenuView):
    template_name = 'quiz_cde/menu_school.html'

    def dispatch_request(self, *args, **kwargs):
        sub_license = _handle_sub_license()
        if sub_license is None:
            return redirect(url_for('.sub_license'))
        return school_views.SchoolMenuView.dispatch_request(self)
