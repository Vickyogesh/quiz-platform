from flask import url_for, session
from .page import Page
from .util import account_url
from .. import access, app


def register_urls_for(bp):
    """Register school views in the blueprint *bp*."""
    bp.route('/s/menu')(Menu.get_view())
    bp.route('/s/statistics')(Statistics.get_view())


class SchoolPage(Page):
    """Base class for school pages."""
    endpoint_prefix = 'school'
    decorators = [access.be_admin_or_school.require()]

    # See client.Statistics and client.ClientStatisticsPage
    def pop_session_helpers(self):
        if 'back_url' in session:
            del session['back_url']
        if 'force_name' in session:
            del session['force_name']


class Menu(SchoolPage):
    """School menu page."""
    default_template = 'ui/menu_school.html'

    def on_request(self):
        str_uid = str(self.uid)
        res = app.account.getSchoolStudents(self.uid)
        account = account_url(with_uid=False)
        self.urls = {
            'add': url_for('api.add_student', id=str_uid),
            'remove': url_for('api.delete_student', id=str_uid, student=0)[:-1],
            'change': account,
            'account': account,
            'stat': url_for('ui.client_statistics', uid="0")[:-1]
        }
        self.pop_session_helpers()
        return self.render(clients=res['students'])


class Statistics(SchoolPage):
    """School statistics page."""
    default_template = 'ui/statistics_school.html'

    @staticmethod
    def _get_ids(data):
        if 'best' not in data or 'worst' not in data:
            return []
        return [x['id'] for x in data['best']] + [x['id'] for x in data['worst']]

    @staticmethod
    def _update_names(users, data):
        for x in data:
            user = users[x['id']]
            x['name'] = user['name']
            x['surname'] = user['surname']

    def on_request(self):
        res = app.core.getSchoolStat(self.quiz_type, self.uid, self.lang)

        # Since res doesn't contain user names then
        # we need to get names from the account service and update result.
        students = res['students']
        lst = Statistics._get_ids(students['current']) \
            + Statistics._get_ids(students['week']) \
            + Statistics._get_ids(students['week3'])
        lst = set(lst)

        if lst:
            data = app.account.getSchoolStudents(self.uid, lst)
            lst = {}
            for info in data['students']:
                lst[info['id']] = info
            Statistics._update_names(lst, students['current']['best'])
            Statistics._update_names(lst, students['current']['worst'])
            Statistics._update_names(lst, students['week']['best'])
            Statistics._update_names(lst, students['week']['worst'])
            Statistics._update_names(lst, students['week3']['best'])
            Statistics._update_names(lst, students['week3']['worst'])

        self.urls = {
            'back': url_for('.school_menu'),
            'account': account_url(with_uid=False),
            'stat': url_for('ui.client_statistics', uid="0")[:-1]
        }
        self.pop_session_helpers()
        return self.render(stat=res)
