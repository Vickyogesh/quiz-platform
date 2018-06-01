from ..bp import core2
from flask import render_template, session, request, url_for, jsonify
from .logic import ExamCore, get_urls
from ..meta import meta, get_quiz_meta
from flask_babelex import lazy_gettext

e = ExamCore(meta)


@core2.route("/exam", methods=['GET'])
def get_exam():
    exam_type = request.args.get('exam_type', None)

    data = e.createExam(session['quiz_id'], session['user']['id'], 'it', exam_type)

    tpl_folder_name = session['quiz_name'] if session['quiz_name'] != 'revisioni' else 'rev'

    return render_template("quiz_{}/exam.html".format(tpl_folder_name),
                           exam=data, quiz_meta=get_quiz_meta(session),
                           user={'account': session['user']},
                           urls=get_urls(session))


@core2.route("/exam/<id>", methods=['POST'])
def save_exam(id):
    data = request.get_json(force=True)
    num_errors = e.saveExam(id, data['questions'], data['answers'], get_quiz_meta(session))
    return jsonify(num_errors=num_errors)
