from flask import session, url_for
from . import ui
from .common import render_template, check_access, account_url
from .. import access


@ui.route('/p/menu')
@check_access
@access.be_client_or_guest.require()
def menu():
    quiz_name = session['quiz_type_name']
    if access.current_user.is_school:
        return render_template('ui/menu_school.html', quiz_name=quiz_name)
    else:
        return render_template('ui/menu_client.html', quiz_name=quiz_name,
                               user=access.current_user,
                               account_url=account_url())


@ui.route('/p/menu/quiz')
@check_access
@access.be_client_or_guest.require()
def menu_quiz():
    quiz_name = session['quiz_type_name']
    quiz_url = url_for('.quiz', topic=0)[:-1]
    return render_template('ui/menu_quiz.html', quiz_name=quiz_name,
                           back_url=url_for('.menu'),
                           quiz_url=quiz_url,
                           user=access.current_user,
                           account_url=account_url())
