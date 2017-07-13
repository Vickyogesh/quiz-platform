from flask import Blueprint, render_template, request, redirect, url_for
from flask import current_app as app
from flask_login import current_user
from .access import logout_user, be_content_manager

cm = Blueprint('cm', __name__, static_folder='./static')

quiz_map = [
    {"name": "B 2011",                  'id': 1},
    {"name": "B 2013",                  'id': 3},
    {"name": "B 2016",                  'id': 50},
    {"name": "CQC",                     'id': 2},
    {"name": "AM",                      'id': 4},
    {"name": "C1 - C1E",                'id': 5},
    {"name": "C1 - C1E code Union 97",  'id': 6},
    {"name": "C - CE",                  'id': 7},
    {"name": "C - CE formerly C1",      'id': 8},
    {"name": "D1 - D1E",                'id': 9},
    {"name": "D - DE",                  'id': 10},
    {"name": "D - DE formerly D1",      'id': 11},
    {"name": "Revisioni AM",            'id': 60},
    {"name": "Revisioni AB",            'id': 61},
    {"name": "Revisioni C1(97) C1E(97)",'id': 62},
    {"name": "Revisioni C1-C1E C-CE",   'id': 63},
    {"name": "Revisioni D1-D1E D-DE",   'id': 64},
    {"name": "Revisioni CQC merci",     'id': 65},
    {"name": "Revisioni CQC persone",   'id': 66}
]


@cm.route("/", methods=['GET'])
@be_content_manager.require()
def index():
    return render_template('content_edit.html',
                           quiz_meta={}, user=current_user, quiz_map=quiz_map)


@cm.route("/question/<quiz_id>/<question_id>", methods=['GET', 'PUT'])
@be_content_manager.require()
def get_question(quiz_id, question_id):
    if request.method == "GET":
        return app.core.getQuestion(quiz_id, question_id)
    elif request.method == "PUT":
        expl = request.form.get('explanation', None)
        return app.core.setExplanation(quiz_id, question_id, expl)


@cm.route("/logout")
@be_content_manager.require()
def logout():
    logout_user()
    return redirect(url_for('index'))