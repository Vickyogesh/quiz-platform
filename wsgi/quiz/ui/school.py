from flask import session, url_for
from . import ui
from .util import render_template, check_access, account_url
from .. import access


def menu():
    quiz_name = session['quiz_type_name']
    return render_template('ui/menu_school.html', quiz_name=quiz_name)


def statistics():
    if access.current_user.is_school:
        return render_template('ui/statistics_school.html')
