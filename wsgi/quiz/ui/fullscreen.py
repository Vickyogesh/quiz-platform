from flask import abort
from . import ui
from .util import render_template, check_access
from .. import access


@ui.route('/c/fmenu')
@check_access
@access.be_client_or_guest.require()
def fullscreen():
    return render_template('ui/fullscreen_wrapper.html', acc_type='c')
