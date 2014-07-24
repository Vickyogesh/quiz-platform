from flask import Blueprint, request, session, render_template
from .. import access

frontend = Blueprint('frontend', __name__,
                     template_folder='templates', static_folder='static',
                     static_url_path='/static/f')


@frontend.route('/', defaults={'quiz_name': 'b2013'})
@frontend.route('/<word:quiz_name>')
def index(quiz_name):
    return render_template('frontend/index.html', quiz_name=quiz_name)


@frontend.route('/<word:quiz_name>/student')
@access.be_client_or_guest.require()
def student(quiz_name):
    return render_template('frontend/student.html', quiz_name=quiz_name)


@frontend.route('/<word:quiz_name>/statistics')
@access.be_user.require()
def statistics(quiz_name):
    return render_template('frontend/statistics.html', quiz_name=quiz_name)


@frontend.route('/<word:quiz_name>/quiz')
@access.be_client_or_guest.require()
def quiz_topics(quiz_name):
    return render_template('frontend/quiz_topics.html', quiz_name=quiz_name)


@frontend.route('/<word:quiz_name>/quiz/<int:topic>')
@access.be_client_or_guest.require()
def quiz(quiz_name, topic):
    return render_template('frontend/quiz.html', quiz_name=quiz_name,
                           topic=topic)


@frontend.route('/<word:quiz_name>/review')
@access.be_client_or_guest.require()
def review(quiz_name):
    return render_template('frontend/review.html', quiz_name=quiz_name)


@frontend.route('/<word:quiz_name>/exam')
@access.be_client_or_guest.require()
def exam(quiz_name):
    return render_template('frontend/exam.html', quiz_name=quiz_name)


@frontend.route('/<word:quiz_name>/exam_statistics')
@access.be_user.require()
def exam_statistics(quiz_name):
    return render_template('frontend/exam_statistics.html',
                           quiz_name=quiz_name)


@frontend.route('/<word:quiz_name>/school')
@access.be_admin_or_school.require()
def school(quiz_name):
    return render_template('frontend/school.html', quiz_name=quiz_name)


@frontend.route('/<word:quiz_name>/school_statistics')
@access.be_admin_or_school.require()
def school_statistics(quiz_name):
    return render_template('frontend/school_statistics.html',
                           quiz_name=quiz_name)
