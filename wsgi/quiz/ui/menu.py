from . import ui, common
from .common import render_template
from .. import access


@ui.route('/<word:quiz_name>/menu')
@common.check_access
@access.be_client_or_guest.require()
def menu(quiz_name):
    if access.current_user.is_school:
        return render_template('ui/menu_school.html', quiz_name=quiz_name)
    else:
        return render_template('ui/menu_client.html', quiz_name=quiz_name,
                               user=access.current_user)
