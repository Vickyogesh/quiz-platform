from flask import Blueprint, request, session, render_template

frontend = Blueprint('frontend', __name__,
                     template_folder='templates', static_folder='static',
                     static_url_path='/static/f')


@frontend.route('/', defaults={'quiz_name': 'b2013'})
@frontend.route('/<word:quiz_name>')
def index(quiz_name):
    return render_template('frontend/index.html', quiz_name=quiz_name)


@frontend.route('/<word:quiz_name>/student')
def student(quiz_name):
    return render_template('frontend/student.html', quiz_name=quiz_name)


@frontend.route('/<word:quiz_name>/statistics')
def statistics(quiz_name):
    return render_template('frontend/statistics.html', quiz_name=quiz_name)


@frontend.route('/<word:quiz_name>/quiz')
def quiz_topics(quiz_name):
    return render_template('frontend/quiz_topics.html', quiz_name=quiz_name)


@frontend.route('/<word:quiz_name>/quiz/<int:topic>')
def quiz(quiz_name, topic):
    return render_template('frontend/quiz.html', quiz_name=quiz_name,
                           topic=topic)


@frontend.route('/<word:quiz_name>/review')
def review(quiz_name):
    return render_template('frontend/review.html', quiz_name=quiz_name)


@frontend.route('/<word:quiz_name>/exam')
def exam(quiz_name):
    return render_template('frontend/exam.html', quiz_name=quiz_name)


@frontend.route('/<word:quiz_name>/exam_statistics')
def exam_statistics(quiz_name):
    return render_template('frontend/exam_statistics.html',
                           quiz_name=quiz_name)


@frontend.route('/<word:quiz_name>/school')
def school(quiz_name):
    return render_template('frontend/school.html', quiz_name=quiz_name)


@frontend.route('/<word:quiz_name>/school_statistics')
def school_statistics(quiz_name):
    return render_template('frontend/school_statistics.html',
                           quiz_name=quiz_name)
