from flask import session, url_for, request, abort
from . import ui
from .util import render_template, check_access, account_url
from .. import access, app


def menu():
    quiz_name = session['quiz_type_name']
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


@ui.route('/p/quiz/<int:topic>')
@check_access
@access.be_client_or_guest.require()
def quiz(topic):
    quiz_name = session['quiz_type_name']
    quiz_type = session['quiz_type']
    lang = request.args.get('lang', 'it')
    force = request.args.get('force', False)

    # TODO: what if x is not int?
    exclude = request.args.get('exclude', None)
    if exclude is not None:
        exclude = exclude.split(',')
        exclude = [int(x) for x in exclude]

    info = app.core.getQuiz(quiz_type, access.current_user.account_id, topic,
                            lang, force, exclude)

    image_url = url_for('img_file', filename='')
    quiz_url = url_for('api.create_quiz', topic=0)[:-1]

    return render_template('ui/quiz.html', quiz_name=quiz_name,
                           back_url=url_for('.menu'),
                           image_url=image_url,
                           quiz_url=quiz_url,
                           user=access.current_user,
                           quiz=info,
                           account_url=account_url())


@ui.route('/p/review')
@check_access
@access.be_client_or_guest.require()
def review():
    quiz_name = session['quiz_type_name']
    quiz_type = session['quiz_type']
    uid = access.current_user.account_id
    lang = request.args.get('lang', 'it')

    # TODO: what if x is not int?
    exclude = request.args.get('exclude', None)
    if exclude is not None:
        exclude = exclude.split(',')
        exclude = [int(x) for x in exclude]

    info = app.core.getErrorReview(quiz_type, uid, lang, exclude)

    image_url = url_for('img_file', filename='')
    quiz_url = url_for('api.get_error_review')

    return render_template('ui/review.html', quiz_name=quiz_name,
                           back_url=url_for('.menu'),
                           image_url=image_url,
                           quiz_url=quiz_url,
                           user=access.current_user,
                           quiz=info,
                           account_url=account_url())


def statistics():
    quiz_name = session['quiz_type_name']
    uid = access.current_user.account_id
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
                           user=access.current_user)


@ui.route('/p/statistics/topic/<int:topic_id>')
@check_access
@access.be_client_or_guest.require()
def statistics_topic(topic_id):
    quiz_name = session['quiz_type_name']
    quiz_type = session['quiz_type']
    lang = request.args.get('lang', 'it')
    uid = access.current_user.account_id
    errors = app.core.getTopicErrors(quiz_type, uid, topic_id, lang)
    return render_template('ui/statistics_client_topic.html',
                           quiz_name=quiz_name,
                           errors=errors,
                           back_url=url_for('.statistics'),
                           account_url=account_url(),
                           user=access.current_user)


@ui.route('/p/statistics/exams/<range>')
@check_access
@access.be_client_or_guest.require()
def statistics_exams(range):
    quiz_name = session['quiz_type_name']
    quiz_type = session['quiz_type']
    uid = access.current_user.account_id
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
                           user=access.current_user)


@ui.route('/p/exam')
@check_access
@access.be_client_or_guest.require()
def exam():
    quiz_name = session['quiz_type_name']
    quiz_type = session['quiz_type']
    user_id = access.current_user.account_id
    lang = request.args.get('lang', 'it')
    exam_type = request.args.get('exam_type', None)
    data = app.core.createExam(quiz_type, user_id, lang, exam_type)

    image_url = url_for('img_file', filename='')
    exam_url = url_for('api.save_exam', id=0)[:-1]
    exam_review_url = url_for('.exam_review', id=0)[:-1]
    return render_template('ui/exam.html', quiz_name=quiz_name,
                           back_url=url_for('.menu'),
                           image_url=image_url,
                           exam_url=exam_url,
                           exam_review_url=exam_review_url,
                           user=access.current_user,
                           exam=data,
                           account_url=account_url())


@ui.route('/p/exam_review/<int:id>')
@check_access
@access.be_client_or_guest.require()
def exam_review(id):
    quiz_name = session['quiz_type_name']
    lang = request.args.get('lang', 'it')
    image_url = url_for('img_file', filename='')
    info = app.core.getExamInfo(id, lang)

    if info['student']['id'] != access.current_user.account_id:
        abort(404)

    return render_template('ui/exam_review.html', quiz_name=quiz_name,
                           back_url=url_for('.menu'),
                           image_url=image_url,
                           user=access.current_user,
                           exam=info,
                           account_url=account_url())
