from flask import session, url_for
from . import ui
from .util import render_template, check_access, account_url
from .. import access, app


def menu():
    quiz_name = session['quiz_type_name']
    uid = access.current_user.account_id
    res = app.account.getSchoolStudents(uid)

    add_url = url_for('api.add_student', id=str(uid))
    remove_url = url_for('api.delete_student', id=str(uid), student=0)[:-1]
    change_url = account_url(with_uid=False)

    return render_template('ui/menu_school.html',
                           quiz_name=quiz_name,
                           clients=res['students'],
                           user=access.current_user,
                           add_url=add_url,
                           remove_url=remove_url,
                           change_url=change_url)


def statistics():
    quiz_name = session['quiz_type_name']
    return render_template('ui/statistics_school.html',
                           quiz_name=quiz_name,
                           user=access.current_user)
