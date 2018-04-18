from ..bp import core2
from flask import render_template, session, request, url_for, jsonify
from .logic import ExamCore
from flask_babelex import lazy_gettext

e = ExamCore()

quiz_meta = {
        'name': 'b',
        'title': lazy_gettext('Quiz B'),
        'exam_meta': {'max_errors': 4, 'total_time': 1800, 'num_questions': 40}
    }


@core2.route("/exam", methods=['GET'])
def get_exam():
    print(session)

    data = e.createExam(session['quiz_id'], session['user']['id'], 'it')
    return render_template("quiz_b/exam.html", exam=data, quiz_meta=quiz_meta, user={'account': session['user']},
                           urls={'exam': url_for('core2.save_exam', id=0)[:-1], 'back': '/ui/'+ session['quiz_name']})


@core2.route("/exam/<id>", methods=['POST'])
def save_exam(id):
    data = request.get_json(force=True)
    num_errors = e.saveExam(id, data['questions'], data['answers'], quiz_meta)
    return jsonify(num_errors=num_errors)
