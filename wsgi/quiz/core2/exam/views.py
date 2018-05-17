from ..bp import core2
from flask import render_template, session, request, url_for, jsonify
from .logic import ExamCore
from ..meta import meta
from flask_babelex import lazy_gettext

e = ExamCore(meta)


@core2.route("/exam", methods=['GET'])
def get_exam():

    data = e.createExam(session['quiz_id'], session['user']['id'], 'it')
    quiz_meta = meta.get(session['quiz_name'])
    if quiz_meta['exam_meta'].get(session['quiz_id']):
        quiz_meta['title'] = quiz_meta['title'][session['quiz_id']]
        quiz_meta['exam_meta'] = quiz_meta['exam_meta'].get(session['quiz_id'])
    return render_template("quiz_{}/exam.html".format(session['quiz_name']),
                           exam=data, quiz_meta=quiz_meta, user={'account': session['user']},
                           urls={'exam': url_for('core2.save_exam', id=0)[:-1], 'back': '/ui/'+ session['quiz_name']})


@core2.route("/exam/<id>", methods=['POST'])
def save_exam(id):
    data = request.get_json(force=True)
    num_errors = e.saveExam(id, data['questions'], data['answers'], meta.get(session['quiz_name']))
    return jsonify(num_errors=num_errors)
