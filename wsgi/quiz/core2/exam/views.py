from ..bp import core2
from flask import render_template, session, request, jsonify
from flask_login import current_user, login_required
from .logic import ExamCore, get_urls
from ..meta import get_quiz_meta
from flask_babelex import gettext

e = ExamCore()


@core2.route("/exam", methods=['GET'])
@login_required
def get_exam():
    quiz_type = int(request.args.get('quiz_type'))
    exam_type = request.args.get('exam_type')

    data = e.createExam(quiz_type, current_user.account_id, 'it', exam_type)

    tpl_folder_name = session['quiz_name'] if session['quiz_name'] != 'revisioni' else 'rev'

    if 'fb_id' in current_user.account:
        fb_data = {
            'id': current_user.account['fb_id'],
            'text': gettext('Number of errors in exam: %%(num)s'),
            'description': 'Quiz Patente',
            'school_title': session.get('extra_school_name'),
            'school_link': session.get('extra_school_url'),
            'school_logo_url': session.get('extra_school_logo_url')
        }
        fb_data = dict((k, v) for k, v in fb_data.iteritems() if v)
    else:
        fb_data = None

    return render_template("quiz_{}/exam.html".format(tpl_folder_name),
                           exam=data, quiz_meta=get_quiz_meta(quiz_type),
                           user={'account': current_user.account},
                           urls=get_urls(quiz_type), fb_data=fb_data)


@core2.route("/exam/<id>", methods=['POST'])
@login_required
def save_exam(id):
    data = request.get_json(force=True)
    num_errors = e.saveExam(id, data['questions'], data['answers'])
    return jsonify(num_errors=num_errors)


@core2.route("/exam_review/<id>", methods=['GET'])
@login_required
def exam_review(id):
    info = e.getExamInfo(id)
    return render_template('common_exam_review.html', exam=info, quiz_meta=get_quiz_meta(info['exam']['quiz_type']),
                           urls=get_urls(info['exam']['quiz_type']), user={'account': current_user.account})