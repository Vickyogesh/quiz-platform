from werkzeug.exceptions import BadRequest, Forbidden
from .wsgi import QuizApp, JSONResponse

app = QuizApp()


@app.get('/quiz/<int:topic>', access=['student', 'guest'])
def create_quiz(topic):
    """ Get 40 questions from the DB and return them to the client. """
    user_id = app.getUserId()
    lang = app.getLang()
    quiz = app.core.getQuiz(user_id, topic, lang)
    return JSONResponse(quiz)


@app.post('/quiz/<int:topic>', access=['student', 'guest'])
def save_quiz(topic):
    """ Save quiz results. """
    user_id = app.getUserId()
    data = app.request.json

    try:
        id_list = data['questions']
        answers = data['answers']
    except KeyError:
        raise BadRequest('Missing parameter.')

    app.core.saveQuiz(user_id, topic, id_list, answers)
    return JSONResponse()


@app.get('/student', access=['student', 'school', 'guest'])
@app.get('/student/<uid:user>', access=['student', 'school', 'guest'])
def get_student_stat(user='me'):
    user_id = app.getUserId(user)
    lang = app.getLang()

    # Student and guest can access only to their own data.
    utype = app.session['user_type']
    uid = app.session['user_id']

    if utype != 'school' and uid != user_id:
        raise Forbidden

    stat = app.core.getUserStat(user_id, lang)
    return JSONResponse(stat)


@app.get('/errorreview', access=['student', 'guest'])
def get_error_review():
    user_id = app.getUserId()
    lang = app.getLang()
    res = app.core.getErrorReview(user_id, lang)
    return JSONResponse(res)


@app.post('/errorreview', access=['student', 'guest'])
def save_error_review():
    user_id = app.getUserId()
    data = app.request.json

    try:
        id_list = data['questions']
        answers = data['answers']
    except KeyError:
        raise BadRequest('Missing parameter.')

    app.core.saveErrorReview(user_id, id_list, answers)
    return JSONResponse()


@app.get('/exam', access=['student', 'guest'])
def create_exam():
    user_id = app.getUserId()
    lang = app.getLang()
    exam = app.core.createExam(user_id, lang)
    return JSONResponse(exam)


@app.post('/exam/<int:id>', access=['student', 'guest'])
def save_exam(id):
    data = app.request.json

    try:
        questions = data['questions']
        answers = data['answers']
    except KeyError:
        raise BadRequest('Missing parameter.')

    app.core.saveExam(id, questions, answers)
    return JSONResponse()


@app.get('/exam/<int:id>', access=['student', 'guest', 'school'])
def get_exam_info(id):
    lang = app.getLang()
    info = app.core.getExamInfo(id, lang)

    # Students can access only to their own data.
    user_id = info['student']['id']
    utype = app.session['user_type']
    uid = app.session['user_id']
    if utype != 'school' and uid != user_id:
        raise Forbidden

    return JSONResponse(info)


@app.get('/student/<uid:user>/exam', access=['student', 'guest', 'school'])
def get_student_exams(user):
    user_id = app.getUserId(user)

    # Students can access only to their own data.
    utype = app.session['user_type']
    uid = app.session['user_id']
    if utype != 'school' and uid != user_id:
        raise Forbidden

    exams = app.core.getExamList(user_id)
    return JSONResponse(exams)


@app.get('/student/<uid:user>/topicerrors/<int:id>',
         access=['student', 'guest', 'school'])
def get_topic_error(user, id):
    user_id = app.getUserId(user)
    lang = app.getLang()

    # Students can access only to their own data.
    utype = app.session['user_type']
    uid = app.session['user_id']
    if utype != 'school' and uid != user_id:
        raise Forbidden

    info = app.core.getTopicErrors(user_id, id, lang)
    return JSONResponse(info)


@app.post('/newschool', access=['admin'])
def add_school():
    data = app.request.json

    try:
        name = data['name']
        login = data['login']
        passwd = data['passwd']
    except KeyError:
        raise BadRequest('Missing parameter.')

    res = app.core.createSchool(name, login, passwd)
    return JSONResponse(res)
