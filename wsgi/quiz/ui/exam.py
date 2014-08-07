from flask import session, url_for, request, abort
from . import ui
from .common import render_template, check_access, account_url
from .. import access, app


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
