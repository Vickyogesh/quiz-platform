from flask import session, request
from . import ui
from .common import render_template, check_access
from .. import app
from ..access import be_client_or_guest, current_user


def client_stat(quiz_name, uid):
    quiz_type = session['quiz_type']
    lang = request.args.get('lang', 'it')
    stat = app.core.getUserStat(quiz_type, uid, lang)
    exams = app.core.getExamList(quiz_type, uid)
    return render_template('ui/statistics_client.html',
                           quiz_name=quiz_name,
                           client_stat=stat,
                           exams=exams,
                           user=current_user)


# TODO: do we need guest statistics?
@ui.route('/<word:quiz_name>/statistics')
@check_access
@be_client_or_guest.require()
def statistics(quiz_name):
    if current_user.is_school:
        return render_template('ui/statistics_school.html', quiz_name=quiz_name)
    else:
        return client_stat(quiz_name, current_user.account_id)
