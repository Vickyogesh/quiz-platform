from ..bp import core2
from flask import render_template, session, request, url_for, jsonify
from .logic import ExamCore, get_urls
from ..meta import meta, get_quiz_meta
from flask_babelex import lazy_gettext

e = ExamCore(meta)


@core2.route("/exam", methods=['GET'])
def get_exam():

    data = e.createExam(session['quiz_id'], session['user']['id'], 'it')

    return render_template("quiz_{}/exam.html".format(session['quiz_name']),
                           exam=data, quiz_meta=get_quiz_meta(session),
                           user={'account': session['user']},
                           urls=get_urls(session))


@core2.route("/exam/<id>", methods=['POST'])
def save_exam(id):
    data = request.get_json(force=True)
    num_errors = e.saveExam(id, data['questions'], data['answers'], get_quiz_meta(session))
    return jsonify(num_errors=num_errors)
