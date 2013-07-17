from werkzeug.exceptions import BadRequest, Forbidden, Unauthorized
from .core.exceptions import QuizCoreError
from .wsgi import QuizApp, JSONResponse

app = QuizApp()


@app.get('/authorize/status')
def get_authorize_status():
    try:
        login = app.session['user_login']
        user = app.core.getUserInfo(login)
    except KeyError:
        raise Unauthorized('Unauthorized.')
    del user['login']
    return JSONResponse({'user': user})


@app.get('/quiz/<int:topic>', access=['student', 'guest'])
def create_quiz(topic):
    """ Get 40 questions from the DB and return them to the client. """
    user_id = app.getUserId()
    lang = app.getLang()
    force = app.request.args.get('force', False)

    exclude = app.request.args.get('exclude', None)
    if exclude is not None:
        try:
            exclude = exclude.split(',')
            exclude = [int(x) for x in exclude]
        except ValueError:
            raise QuizCoreError('Invalid parameters.')

    quiz = app.core.getQuiz(app.quiz_type, user_id, topic, lang, force, exclude)
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

    app.core.saveQuiz(app.quiz_type, user_id, topic, id_list, answers)
    return JSONResponse()


@app.get('/student', access=['student', 'school', 'guest'])
@app.get('/student/<uid:user>', access=['student', 'school', 'guest'])
def get_student_stat(user='me'):
    user_id = app.getUserId(user)
    lang = app.getLang()

    uid = app.getUserId()
    utype = app.session['user_type']

    stat = app.core.getUserStat(app.quiz_type, user_id, lang)

    # School can access to it's students only.
    if utype == 'school' and (user == 'me' or uid != stat['student']['school_id']):
        raise Forbidden('Forbidden.')

    # Students can access only to their own exams.
    elif utype != 'school' and uid != stat['student']['id']:
        raise Forbidden('Forbidden.')

    data = app.account.getStudent(user_id)['account']
    info = stat['student']
    info['name'] = data['name']
    info['surname'] = data['surname']
    return JSONResponse(stat)


@app.get('/errorreview', access=['student', 'guest'])
def get_error_review():
    user_id = app.getUserId()
    lang = app.getLang()

    exclude = app.request.args.get('exclude', None)
    if exclude is not None:
        try:
            exclude = exclude.split(',')
            exclude = [int(x) for x in exclude]
        except ValueError:
            raise QuizCoreError('Invalid parameters.')

    res = app.core.getErrorReview(app.quiz_type, user_id, lang, exclude)
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

    app.core.saveErrorReview(app.quiz_type, user_id, id_list, answers)
    return JSONResponse()


@app.get('/exam', access=['student', 'guest'])
def create_exam():
    user_id = app.getUserId()
    lang = app.getLang()
    exam = app.core.createExam(app.quiz_type, user_id, lang)
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

    exams = app.core.getExamList(app.quiz_type, user_id)

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

    info = app.core.getTopicErrors(app.quiz_type, user_id, id, lang)

    # School can access to exams of it's students only.
    if utype == 'school' and uid != info['student']['school_id']:
        raise Forbidden('Forbidden.')
    return JSONResponse(info)


@app.get('/admin/schools', access=['admin'])
def school_list():
    res = app.account.getSchools()
    return JSONResponse(res)


@app.post('/admin/newschool', access=['admin'])
def add_school():
    res = app.account.addSchool(raw=app.request.data)
    return JSONResponse(res)


@app.post('/admin/school/<int:id>', access=['admin'])
@app.delete('/admin/school/<int:id>', access=['admin'])
def delete_school(id):
    if app.request.method == 'POST':
        action = app.request.args.get('action', None)
        if action != 'delete':
            raise BadRequest('Invalid action.')
        elif len(app.request.data):
            raise BadRequest('Invalid request.')

    res = app.account.removeSchool(id)

    if res['status'] == 200:
        res = app.core.deleteSchool(id)
    return JSONResponse(res)


@app.get('/school/<uid:id>/students', access=['school', 'admin'])
def student_list(id):
    school_id = app.getUserId(id)
    res = app.account.getSchoolStudents(school_id)
    return JSONResponse(res)


@app.post('/school/<uid:id>/newstudent', access=['school', 'admin'])
def add_student(id):
    school_id = app.getUserId(id)
    res = app.account.addStudent(school_id, raw=app.request.data)
    return JSONResponse(res)


@app.post('/school/<uid:id>/student/<int:student>', access=['school', 'admin'])
@app.delete('/school/<uid:id>/student/<int:student>', access=['school', 'admin'])
def delete_student(id, student):
    if app.request.method == 'POST':
        action = app.request.args.get('action', None)
        if action != 'delete':
            raise BadRequest('Invalid action.')
        elif len(app.request.data):
            raise BadRequest('Invalid request.')

    id = app.getUserId(id)
    res = app.account.removeStudent(student)

    # Remove student from local DB if he was removed from accounts.
    if res['status'] == 200:
        app.core.deleteStudent(student)

    return JSONResponse(res)


def _get_ids(data):
    if 'best' not in data or 'worst' not in data:
        return []
    return [x['id'] for x in data['best']] + [x['id'] for x in data['worst']]


def _update_names(users, data):
    for x in data:
        user = users[x['id']]
        x['name'] = user['name']
        x['surname'] = user['surname']


@app.get('/school/<uid:id>', access=['school', 'admin'])
def school_stat(id):
    school_id = app.getUserId(id)

    if not app.isAdmin():
        uid = app.session['user_id']
        if uid != school_id:
            raise Forbidden('Forbidden.')
    elif id == 'me':
        raise Forbidden('Forbidden.')

    lang = app.getLang()
    res = app.core.getSchoolStat(app.quiz_type, school_id, lang)

    # Since res doesn't contain user names then
    # we need to get names from the account service and update result.
    students = res['students']
    lst = _get_ids(students['current']) \
        + _get_ids(students['week']) \
        + _get_ids(students['week3'])
    lst = set(lst)

    if lst:
        data = app.account.getSchoolStudents(school_id, lst)
        lst = {}
        for info in data['students']:
            lst[info['id']] = info
        _update_names(lst, students['current']['best'])
        _update_names(lst, students['current']['worst'])
        _update_names(lst, students['week']['best'])
        _update_names(lst, students['week']['worst'])
        _update_names(lst, students['week3']['best'])
        _update_names(lst, students['week3']['worst'])

    return JSONResponse(res)
