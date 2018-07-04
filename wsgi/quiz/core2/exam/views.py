from ..bp import core2
from flask import render_template, session, request, jsonify
from .logic import ExamCore, get_urls
from ..meta import get_quiz_meta
from flask_babelex import lazy_gettext

e = ExamCore()


@core2.route("/exam", methods=['GET'])
def get_exam():
    quiz_type = int(request.args.get('quiz_type'))
    exam_type = request.args.get('exam_type')

    data = e.createExam(quiz_type, session['user']['id'], 'it', exam_type)

    tpl_folder_name = session['quiz_name'] if session['quiz_name'] != 'revisioni' else 'rev'

    return render_template("quiz_{}/exam.html".format(tpl_folder_name),
                           exam=data, quiz_meta=get_quiz_meta(quiz_type),
                           user={'account': session['user']},
                           urls=get_urls(session))


@core2.route("/exam/<id>", methods=['POST'])
def save_exam(id):
    data = request.get_json(force=True)
    num_errors = e.saveExam(id, data['questions'], data['answers'])
    return jsonify(num_errors=num_errors)


@core2.route("/exam_review/<id>", methods=['GET'])
def exam_review(id):
    info = e.getExamInfo(id)
    return render_template('common_exam_review.html', exam=info, quiz_meta=get_quiz_meta(session),
                           urls=get_urls(session), user={'account': session['user']})