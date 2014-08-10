from flask import url_for, request, abort
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


class Menu(SchoolPage):
    """School menu page."""
    template_name = 'ui/menu_school.html'

    def on_request(self):
        str_uid = str(self.uid)
        res = app.account.getSchoolStudents(self.uid)
        account = account_url(with_uid=False)
        self.urls = {
            'add': url_for('api.add_student', id=str_uid),
            'remove': url_for('api.delete_student', id=str_uid, student=0)[:-1],
            'change': account,
            'account': account
        }
        return self.render(clients=res['students'])


class Statistics(SchoolPage):
    """School statistics page."""
    template_name = 'ui/statistics_school.html'

    def on_request(self):
        return self.render()
