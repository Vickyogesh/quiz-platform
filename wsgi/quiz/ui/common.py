from . import ui
from . import school, client
from .util import check_access
from .. import access


@ui.route('/p/menu')
@check_access
@access.be_user.require()
def menu():
    if access.current_user.is_school:
        return school.menu()
    else:
        return client.menu()


# TODO: do we need guest statistics?
@ui.route('/p/statistics')
@check_access
@access.be_user.require()
def statistics():
    if access.current_user.is_school:
        return school.statistics()
    else:
        return client.statistics()
