from flask import url_for, session
from .page import PageView, PageModel, PagesMetadata, register_pages
from .util import account_url
from .. import access, app


class BaseSchoolModel(PageModel):
    # See client.Statistics and client.ClientStatisticsPage
    def pop_session_helpers(self):
        if 'back_url' in session:
            del session['back_url']
        if 'force_name' in session:
            del session['force_name']


class MenuModel(BaseSchoolModel):
    template = 'ui/menu_school.html'

    def on_request(self):
        str_uid = str(self.page.uid)
        res = app.account.getSchoolStudents(self.page.uid)
        account = account_url(with_uid=False)
        self.page.urls = {
            'add': url_for('api.add_student', id=str_uid),
            'remove': url_for('api.delete_student', id=str_uid, student=0)[:-1],
            'change': account,
            'account': account,
            'stat': url_for('ui.client_statistics', uid="0")[:-1]
        }
        self.pop_session_helpers()
        return self.page.render(clients=res['students'])


class StatisticsModel(BaseSchoolModel):
    template = 'ui/statistics_school.html'

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
        res = app.core.getSchoolStat(self.page.quiz_id, self.page.uid,
                                     self.page.lang)

        # Since res doesn't contain user names then
        # we need to get names from the account service and update result.
        students = res['students']
        lst = StatisticsModel._get_ids(students['current']) \
            + StatisticsModel._get_ids(students['week']) \
            + StatisticsModel._get_ids(students['week3'])
        lst = set(lst)

        if lst:
            data = app.account.getSchoolStudents(self.page.uid, lst)
            lst = {}
            for info in data['students']:
                lst[info['id']] = info
            StatisticsModel._update_names(lst, students['current']['best'])
            StatisticsModel._update_names(lst, students['current']['worst'])
            StatisticsModel._update_names(lst, students['week']['best'])
            StatisticsModel._update_names(lst, students['week']['worst'])
            StatisticsModel._update_names(lst, students['week3']['best'])
            StatisticsModel._update_names(lst, students['week3']['worst'])

        self.page.urls = {
            'back': url_for('.school_menu'),
            'account': account_url(with_uid=False),
            'stat': url_for('ui.client_statistics', uid="0")[:-1]
        }
        self.pop_session_helpers()
        return self.page.render(stat=res)


class SchoolPage(PageView):
    """Base class for school pages."""
    endpoint_prefix = 'school'
    decorators = [access.be_admin_or_school.require()]


class MenuView(SchoolPage):
    default_model = MenuModel
    rules = ({'rule': '/s/menu'},)


class StatisticsView(SchoolPage):
    default_model = StatisticsModel
    rules = ({'rule': '/s/statistics'},)


class SchoolPagesMetadata(PagesMetadata):
    name = 'school'


# School pages.
page_views = {
    'menu': MenuView,
    'statistics': StatisticsView
}


def register_views(bp):
    """Register school views in the blueprint *bp*."""
    register_pages(bp, page_views, [SchoolPagesMetadata])
