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

    uid = app.getUserId()
    utype = app.session['user_type']

    stat = app.core.getUserStat(user_id, lang)

    # School can access to it's students only.
    if utype == 'school' and (user == 'me' or uid != stat['student']['school_id']):
        raise Forbidden('Forbidden.')

    # Students can access only to their own exams.
    elif utype != 'school' and uid != stat['student']['id']:
        raise Forbidden('Forbidden.')

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

    uid = app.getUserId()
    utype = app.session['user_type']

    # School can access to exams of it's students only.
    if utype == 'school' and uid != info['student']['school_id']:
        raise Forbidden('Forbidden.')

    # Students can access only to their own exams.
    elif utype != 'school' and uid != info['student']['id']:
        raise Forbidden('Forbidden.')

    return JSONResponse(info)


@app.get('/student/<uid:user>/exam', access=['student', 'guest', 'school'])
def get_student_exams(user):
    user_id = app.getUserId(user)

    # Students can access only to their own data.
    uid = app.getUserId()
    utype = app.session['user_type']

    if utype == 'school' and user == 'me':
        raise Forbidden('Forbidden.')
    elif utype != 'school' and uid != user_id:
        raise Forbidden('Forbidden.')

    exams = app.core.getExamList(user_id)

    # School can access to exams of it's students only.
    if utype == 'school' and uid != exams['student']['school_id']:
        raise Forbidden('Forbidden.')

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
        raise Forbidden('Forbidden.')

    info = app.core.getTopicErrors(user_id, id, lang)

    # School can access to exams of it's students only.
    if utype == 'school' and uid != info['student']['school_id']:
        raise Forbidden('Forbidden.')

    return JSONResponse(info)


@app.get('/admin/schools', access=['admin'])
def school_list():
    res = app.core.getSchoolList()
    return JSONResponse(res)


@app.post('/admin/newschool', access=['admin'])
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


@app.post('/admin/school/<int:id>', access=['admin'])
@app.delete('/admin/school/<int:id>', access=['admin'])
def delete_school(id):
    if app.request.method == 'POST':
        action = app.request.args.get('action', None)
        if action != 'delete':
            raise BadRequest('Invalid action.')
        elif app.request.data is not None:
            raise BadRequest('Invalid request.')

    res = app.core.deleteSchool(id)
    return JSONResponse(res)


@app.get('/school/<uid:id>/students', access=['school', 'admin'])
def student_list(id):
    school_id = app.getUserId(id)

    if not app.isAdmin():
        uid = app.session['user_id']
        if uid != school_id:
            raise Forbidden('Forbidden.')
    elif id == 'me':
        raise Forbidden('Forbidden.')

    res = app.core.getStudentList(school_id)
    return JSONResponse(res)


@app.post('/school/<uid:id>/newstudent', access=['school'])
def add_student(id):
    school_id = app.getUserId(id)
    data = app.request.json

    uid = app.session['user_id']
    if uid != school_id:
        raise Forbidden('Forbidden.')

    try:
        name = data['name']
        surname = data['surname']
        login = data['login']
        passwd = data['passwd']
    except KeyError:
        raise BadRequest('Missing parameter.')

    res = app.core.createStudent(name, surname, login, passwd, school_id)
    return JSONResponse(res)


@app.post('/school/<uid:id>/student/<int:student>', access=['school'])
@app.delete('/school/<uid:id>/student/<int:student>', access=['school'])
def delete_student(id, student):
    if app.request.method == 'POST':
        action = app.request.args.get('action', None)
        if action != 'delete':
            raise BadRequest('Invalid action.')
        elif app.request.data is not None:
            raise BadRequest('Invalid request.')

    school_id = app.getUserId(id)
    uid = app.session['user_id']
    if uid != school_id:
        raise Forbidden('Forbidden.')

    res = app.core.deleteStudent(id, student)
    return JSONResponse(res)
