from flask import session, request, url_for
from . import ui
from .common import render_template, check_access, account_url
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
                           back_url=url_for('.menu'),
                           account_url=account_url(),
                           user=current_user)


# TODO: do we need guest statistics?
@ui.route('/p/statistics')
@check_access
@be_client_or_guest.require()
def statistics():
    quiz_name = session['quiz_type_name']
    if current_user.is_school:
        return render_template('ui/statistics_school.html')
    else:
        return client_stat(quiz_name, current_user.account_id)


@ui.route('/p/statistics/topic/<int:topic_id>')
@check_access
@be_client_or_guest.require()
def statistics_topic(topic_id):
    quiz_name = session['quiz_type_name']
    quiz_type = session['quiz_type']
    lang = request.args.get('lang', 'it')
    uid = current_user.account_id
    errors = app.core.getTopicErrors(quiz_type, uid, topic_id, lang)
    return render_template('ui/statistics_client_topic.html',
                           quiz_name=quiz_name,
                           errors=errors,
                           back_url=url_for('.statistics'),
                           account_url=account_url(),
                           user=current_user)


@ui.route('/p/statistics/exams/<range>')
@check_access
@be_client_or_guest.require()
def statistics_exams(range):
    quiz_name = session['quiz_type_name']
    quiz_type = session['quiz_type']
    uid = current_user.account_id
    exams = app.core.getExamList(quiz_type, uid)['exams']
    total = 40  # TODO: some quizzes has different value

    exam_url = url_for('api.get_exam_info', id=0)[:-1]
    image_url = url_for('img_file', filename='')

    range_exams = exams.get(range)
    if range_exams is None:
        range_exams = exams['week3']
        range_exams.extend(exams['week'])
        range_exams.extend(exams['current'])

    return render_template('ui/statistics_client_exams.html',
                           quiz_name=quiz_name,
                           back_url=url_for('.statistics'),
                           account_url=account_url(),
                           exams=range_exams,
                           total=total,
                           exam_url=exam_url,
                           image_url=image_url,
                           user=current_user)
