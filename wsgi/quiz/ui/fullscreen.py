from flask import request, redirect, url_for
from . import ui
from .util import render_template, check_access
from .. import access


def is_mobile():
    p = request.user_agent.platform

    if p == 'android' or p == 'iphone' or p == 'ipad' or \
       (p == 'windows' and 'Phone' in request.user_agent.string):
        return True
    return False


@ui.route('/c/fmenu')
@check_access
@access.be_client_or_guest.require()
def fullscreen():
    if is_mobile():
        return redirect(url_for('.client_menu'))
    else:
        return render_template('ui/fullscreen_wrapper.html')
