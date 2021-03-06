"""
This module provides common school related quiz views.
"""
from flask import url_for, request, current_app, session
from flask_login import current_user
from .base import BaseView, account_url
from .. import access


class SchoolView(BaseView):
    """Base school page view.

    It adds account URl to the template and performs school permission check.
    """
    decorators = [access.be_admin_or_school.require()]

    def page_urls(self):
        return {'account': account_url(with_uid=False)}

    @staticmethod
    def pop_session_helpers():
        """Helper function to cleanup session from
        :class:`back_url <.client_views.ClientStatisticsView>` and
        :class:`force_name <.client_views.ClientStatisticsBase>`.
        """
        session.pop('back_url', None)
        session.pop('force_name', None)


class SchoolMenuView(SchoolView):
    """Common school menu view.

    It adds extra URLs to the template and renders school's client list.

    Note:
        May be used without changes for various quiz types.
    """
    template_name = 'common_menu_school.html'
    url_rule = '/school/menu'
    endpoint = 'school_menu'

    def __init__(self):
        # Used to create back url depending on request.
        self._uid = None

    def page_urls(self):
        urls = SchoolView.page_urls(self)
        urls['add'] = url_for('api.add_student', id=self._uid)
        urls['remove'] = url_for('api.delete_student', id=self._uid,
                                 student=0)[:-1]
        urls['change'] = urls['account']
        urls['stat'] = url_for('.client_statistics', uid="0")[:-1]
        return urls

    def dispatch_request(self):
        uid = current_user.account_id
        self._uid = str(uid)
        self.pop_session_helpers()
        res = current_app.account.getSchoolStudents(uid)
        return self.render_template(clients=res['students'])


class SchoolStatisticsView(SchoolView):
    """Common school statistics view.

    It adds extra URLs to the template and renders common school statistics.
    """
    template_name = 'common_statistics_school.html'
    url_rule = '/school/statistics'
    endpoint = 'school_statistics'

    @staticmethod
    def _get_ids(data):
        if 'best' not in data or 'worst' not in data:
            return []
        return [x['id'] for x in data['best']] + [x['id'] for x in data['worst']]

    @staticmethod
    def _update_names(users, data):
        for x in data:
            user = users.get(x['id'])
            if user is not None:
                x['name'] = user['name']
                x['surname'] = user['surname']

    def page_urls(self):
        urls = SchoolView.page_urls(self)
        urls['back'] = url_for('.school_menu')
        urls['stat'] = url_for('.client_statistics', uid="0")[:-1]
        return urls

    def dispatch_request(self):
        uid = current_user.account_id
        res = current_app.core.getSchoolStat(self.meta['id'], uid,
                                             self.request_lang)

        # Since res doesn't contain user names then
        # we need to get names from the account service and update result.
        students = res['students']
        lst = self._get_ids(students['current']) \
            + self._get_ids(students['week']) \
            + self._get_ids(students['week3'])
        lst = set(lst)

        if lst:
            data = current_app.account.getSchoolStudents(uid, lst)
            lst = {}
            for info in data['students']:
                lst[info['id']] = info
            self._update_names(lst, students['current']['best'])
            self._update_names(lst, students['current']['worst'])
            self._update_names(lst, students['week']['best'])
            self._update_names(lst, students['week']['worst'])
            self._update_names(lst, students['week3']['best'])
            self._update_names(lst, students['week3']['worst'])

        self.pop_session_helpers()
        return self.render_template(stat=res)
