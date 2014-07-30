from . import ui
from .common import render_template, check_access, account_url
from .. import access


@ui.route('/<word:quiz_name>/menu')
@check_access
@access.be_client_or_guest.require()
def menu(quiz_name):
    if access.current_user.is_school:
        return render_template('ui/menu_school.html', quiz_name=quiz_name)
    else:
        return render_template('ui/menu_client.html', quiz_name=quiz_name,
                               user=access.current_user,
                               account_url=account_url())
