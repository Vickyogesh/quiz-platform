from ..bp import core2
from flask import render_template, session
# from ..models import Question


@core2.route("/exam")
def exam():
    # print(Question.query.get(1))
    return render_template("quiz_b/exam.html")