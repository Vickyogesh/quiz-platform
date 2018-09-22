from functools import wraps
import requests
from werkzeug.exceptions import BadRequest
from werkzeug.urls import url_encode, Href
from flask import current_app as app
from flask import Blueprint, request, session, Response, redirect, abort, g, json, url_for
from .appcore import json_response, dict_to_json_response
from .core.exceptions import QuizCoreError
from . import access
from .access import current_user, OwnerPermission
from .common.base import registered_quiz_meta

api = Blueprint('api', __name__)

@api.before_request
def get_quiz_meta():
    uid = session.get('quiz_id', None)
    if uid is not None:
        # truck quiz has special meta object which covers multiple items.
        if 5 <= uid <= 11:
            uid = 5
        elif 60 <= uid <= 66:
            uid = 60
        g.quiz_meta = registered_quiz_meta[uid]


_ifix_html = """<!DOCTYPE html>
<html>
<body>
<script>top.location = "{0}"</script>
</body>
</html>
"""


def count_user_access(handle_guest=True):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = current_user
            if not user.is_anonymous() and user.is_school_member:
                quiz_id = session['quiz_id']
                sid = user.account['school_id']
                uid = user.account_id
                user_type = user.user_type
                app.core.updateUserLastVisit(quiz_id, uid, user_type, sid)
                if handle_guest and user.is_guest:
                    if not app.core.processGuestAccess(quiz_id, uid):
                        abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator


def get_user_id(uid=None):
    """Get user ID based on uid value.

    If uid is None or 'me' then session's user ID will be returned,
    otherwise uid itself will be returned.
    """
    return current_user.account_id if uid is None or uid == 'me' else long(uid)


# Workaround to solve Safari 3rd party cookie blocking for iframe:
#
# NOTE: beaker sessions dependent solution!
@api.route('/ifix')
def iframe_fix():
    """Workaround to solve Safari 3rd party cookie blocking for iframe.

    Return a page wich redirects to the `next` URL.

    .. sourcecode:: http

        GET /ifix?next=someurl.com HTTP/1.1

    :query next: Redirect URL.

    .. seealso::
        http://kb.imakewebsites.ca/2013/04/30/safari-3rd-party-cookies-and-facebook-apps/
    """
    next_url = request.args.get('next')
    session['ensure_session'] = True  # to have 'cookie_out' in session.
    if next_url is None:
        raise BadRequest('Missing argument.')
    r = Response(_ifix_html.format(next_url), mimetype='text/html')
    r.headers['Set-Cookie'] = session._headers['cookie_out']
    return r


@api.route('/accounturl')
def get_account_url():
    """Redirect to the account's page on the **Accounts service**.

    .. sourcecode:: http

        GET /accounturl HTTP/1.1
    """
    url, cid = app.account.getUserAccountPage()
    args = request.args.copy()
    args['cid'] = cid
    return redirect(url + '?' + url_encode(args))


@api.route('/userinfo')
def get_authorize_status():
    """Current user info.

    **Example request**:

    .. sourcecode:: http

       GET /userinfo HTTP/1.1

    .. note::
        It sends request to the **Accounts Service**. See it's web API docs.
    """
    info = app.account.getUserInfo()
    return dict_to_json_response(info)


@api.route('/fbcanvas/<path>/', methods=['GET', 'POST'])
def fb_canvas(path):
    """Facebook canvas support."""
    hr = Href(request.host_url + path + '/')
    args = request.args.copy()
    args['fblogin'] = 1
    return redirect(hr(args))


@api.route('/link_facebook', methods=['POST'])
@access.be_client.require()
@count_user_access()
def link_facebook():
    """Link user to the facebook account.

    **Access**: student.

    **Example request**:

    .. sourcecode:: http

       POST /userinfo HTTP/1.1
       Content-Type: application/json

       {"userId": 123}

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json
        {"status": 200}

    :<json int userId: user ID.

    .. note::
        It sends request to the **Accounts Service**. See it's web API docs.
    """
    data = request.get_json(force=True)
    try:
        user_id = data['userId']
    except KeyError:
        raise BadRequest('Missing parameter.')
    res = app.account.linkFacebookAccount(user_id)
    current_user.account['fb_id'] = user_id
    return dict_to_json_response(res)


@api.route('/link_instagram', methods=['GET'])
@access.be_client.require()
@count_user_access()
def link_instagram():

    from .views import ig_api
    r_url = 'https://quiztest.editricetoni.it/instagram_callback'
    print(r_url)
    url = requests.Request('GET',
                           r_url,
                           params=dict(id=current_user.account_id)).\
        prepare().url
    ig_api.redirect_uri = url
    print(url)
    url = ig_api.get_authorize_url()
    return redirect(url)


# @api.route('/signup_instagram', methods=['POST'])
# @access.be_client.require()
# @count_user_access()
# def signup_instagram():
#     ig_code = request.json['code']
#     print(ig_code)
#     if not user_id:
#         raise BadRequest('Missing Parameter')
#
#     return 'ig sign up'


@api.route('/quiz/<int:topic>')
@access.be_client_or_guest.require()
@count_user_access()
def create_quiz(topic):
    """Get 40 questions from the DB and return them to the client.

    **Access**: student, guest.

    **Example requests**:

    .. sourcecode:: http

       GET /quiz/1 HTTP/1.1

    .. sourcecode:: http

       GET /quiz/42?lang=de&force=1&exclude=12,333,232 HTTP/1.1

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: application/json

       {
            "status": 200,
            "topic": 1,
            "questions": [
                {
                    "answer": 0,
                    "text": "Question text1",
                    "image": 234,
                    "id": 12
                },
                {
                    "answer": 1,
                    "text": "Question text2",
                    "image": 34,
                    "id": 3,
                    "image_bis": "b"
                },
                {
                    "answer": 1,
                    "text": "Question text3",
                    "id": 108
                }
            ]
       }

    :arg topic_id: Topic for which questions are requested.

    :query lang: Question language: *it*, *fr*, *de*. Optional, default is *it*.
    :query force: Reset quiz if all questions are answered.
    :query exclude: List of questions to exclude.

    :>json int status: Response status.
    :>json int topic: Topic ID.
    :>json list questions: List of questions.
    :>json int question.answer: Question answer: 0 - false, 1 - true.
    :>json string question.text: Question text.
    :>json int question.image: Question image name.
    :>json int question.id: Question ID.
    :>json string question.image_bis: Image part.

    :statuscode 200: Everything is ok.
    :statuscode 401: Login required.
    :statuscode 403: See **access**.
    :statuscode 400: Invalid parameters.

    .. note::
        Empty questions list means what all questions are answered and quiz
        reset is required if you want to get quiz again.
    """
    user_id = get_user_id()
    lang = request.args.get('lang', 'it')
    force = request.args.get('force', False)
    exclude = request.args.get('exclude', None)
    topic_lst = request.args.get('t_lst')

    if exclude is not None:
        try:
            exclude = exclude.split(',')
            exclude = [int(x) for x in exclude]
        except ValueError:
            raise QuizCoreError('Invalid parameters.')
    if topic_lst is not None:
        try:
            topic_lst = topic_lst.split(',')
            topic_lst = [int(t) for t in topic_lst]
        except ValueError:
            raise QuizCoreError('Invalid parameters.')
    quiz = app.core.getQuiz(session['quiz_id'], user_id, topic, lang, force,
                            exclude, topic_lst=topic_lst)
    return dict_to_json_response(quiz)


@api.route('/quiz_by_image/<int:image>')
@access.be_client_or_guest.require()
@count_user_access()
def quiz_by_image(image):
    from .core2 import QuizCore
    q = QuizCore()
    quiz = q.getQuizByImage(image)
    return dict_to_json_response(quiz)


@api.route('/get_ai_question', methods=['POST'])
@access.be_client_or_guest.require()
@count_user_access()
def get_ai_question():
    user_id = get_user_id()
    data = request.get_json(force=True)
    data['u_id'] = user_id
    res = app.core.getAiQuestion(data)
    return dict_to_json_response(res, status=res['status'])


@api.route('/post_ai_answer', methods=['POST'])
@access.be_client_or_guest.require()
@count_user_access()
def post_ai_answer():
    data = request.get_json(force=True)
    return dict_to_json_response(app.core.postAiAnswer(data))


@api.route('/quiz/<int:topic>', methods=['POST'])
@access.be_client_or_guest.require()
@count_user_access()
def save_quiz(topic):
    """Save quiz results for the specified ``topic``.

    Client sends list of answered questions and answers.
    List of questions is not fixed to 40.

    **Access**: student, guest.

    **Example request**:

    .. sourcecode:: http

       POST /quiz/1 HTTP/1.1
       Content-Type: application/json

       {"questions": [1,2,3,10], "answers": [1,0,0,1]}

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: application/json; charset=utf-8

       {"status": 200}

    :arg topic: Quiz topic.

    :<json list questions: List of questions IDs with answers.
    :<json list answers: List of answers for the `questions`; 0 - false,
        1 - true. *Number of answers must be the same as questions.*

    :>json int status: Response status.

    :statuscode 200: Everything is ok.
    :statuscode 401: Login required.
    :statuscode 403: See **access**.
    :statuscode 400: Not a JSON. Client sent malformed JSON string.
    :statuscode 400: Missing parameter. At least one of the parameters missing.
    :statuscode 400: Parameters length mismatch.
        Lists has different numbers of elements.
    :statuscode 400: Empty list.
    :statuscode 400: Invalid value. List element is not a number.
    :statuscode 400: Already answered.
        Answers already sent to the server for the current quiz.
    """
    user_id = get_user_id()
    data = request.get_json(force=True)
    try:
        id_list = data['questions']
        answers = data['answers']
    except KeyError:
        raise BadRequest('Missing parameter.')
    app.core.saveQuiz(session['quiz_id'], user_id, topic, id_list, answers)
    return json_response()


@api.route('/student', defaults={'user': 'me'})
@api.route('/student/<uid:user>')
@access.be_user.require()
@count_user_access()
def get_student_stat(user):
    """Get statistics for the student with specified ID.
    If ``user`` is *me* then current user ID is used.

    **Access**: school, student, guest.

    **Example requests**:

    .. sourcecode:: http

       GET /student/1 HTTP/1.1

    .. sourcecode:: http

       GET /student/me HTTP/1.1

    .. sourcecode:: http

       GET /student/42?lang=de HTTP/1.1

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: application/json

       {
         "status": 200,
         "student": {
           "id": 42,
           "name": "Chuck",
           "surname": "Norris"
         },
         "exams": {
             "current": 10,
             "week": 80,
             "week3": 35
         },
         "topics": [
           {
             "id": 1,
             "text": "Topic 1",
             "errors": {
               "current": 12,
               "week": 34.5,
               "week3": -1
             }
           }
         ]
       }

    :arg user: User ID or *me*.

    :query lang: Statistics language, default is *it*.

    :>json int status: Response status.

    :>json dict student: Student account info.
    :>json int student.id: Account ID.
    :>json string student.name: Account name.
    :>json string student.surname: Account surname.

    :>json dict exams: Student exams statistics.
    :>json dict exams.current: Percent of current exams errors.
    :>json dict exams.week: Percent of the last week exam errors.
    :>json dict exams.week3: Percent of the 7 weeks before
        last week exam errors.

    :>json list topics: List of topics statistics.
    :>json int topics.id: Topic ID.
    :>json int topics.text: Topic text.
    :>json dict topics.errors: Errors history. See ``exams`` ranges.

    :statuscode 200: Everything is ok.
    :statuscode 401: Login required.
    :statuscode 403: See **access**.
    :statuscode 400: Unknown student: user with specified **id** is not present.
    :statuscode 400: Not a student: user with specified **id** is not a student.

    .. note::
        It sends request to the **Accounts Service** to get ``student``.
    """
    user_id = get_user_id(user)  # requested user
    lang = request.args.get('lang', 'it')
    stat = app.core.getUserStat(session['quiz_id'], user_id, lang)

    # School can access to it's students only.
    if (current_user.is_school and (user == 'me' or
       not OwnerPermission(stat['student']['school_id']).can())):
        raise abort(403)
    # Students can access only to their own exams.
    elif current_user.is_school_member and not OwnerPermission(user_id).can():
        raise abort(403)

    data = app.account.getStudent(user_id)['account']
    info = stat['student']
    info['name'] = data['name']
    info['surname'] = data['surname']
    return dict_to_json_response(stat)


@api.route('/errorreview')
@access.be_client_or_guest.require()
@count_user_access()
def get_error_review():
    """Get error review questions.

    **Access**: student, guest.

    **Example requests**:

    .. sourcecode:: http

       GET /errorreview HTTP/1.1

    .. sourcecode:: http

       GET /errorreview?lang=fr&exclude=12,33 HTTP/1.1

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: application/json; charset=utf-8

       {
         "status": 200,
         "questions": [
           {
             "answer": 0,
             "text": "Question text1",
             "image": 234,
             "id": 12
           }
         ]
       }

    :query lang: Questions language, default: *it*.
    :query exclude: List of questions to exclude.

    :>json int status: Response status.
    :>json list questions: Error review questions.
        See :http:get:`/v1/quiz/(int:topic)`.

    :statuscode 200: Everything is ok.
    :statuscode 400: Invalid parameters.
    :statuscode 401: Login required.
    :statuscode 403: See **access**.

    .. note::
        Empty question list means what all questions answered correctly or no
        answers provided yet.
    """
    user_id = get_user_id()
    lang = request.args.get('lang', 'it')
    exclude = request.args.get('exclude', None)
    if exclude is not None:
        try:
            exclude = exclude.split(',')
            exclude = [int(x) for x in exclude]
        except ValueError:
            raise QuizCoreError('Invalid parameters.')
    res = app.core.getErrorReview(session['quiz_id'], user_id, lang, exclude)
    return dict_to_json_response(res)


@api.route('/errorreview', methods=['POST'])
@access.be_client_or_guest.require()
@count_user_access()
def save_error_review():
    """Send answers for the error review questions.
    List of questions is not fixed to 40.

    **Access**: student, guest.

    **Example request**:

    .. sourcecode:: http

       POST /errorreview HTTP/1.1
       Content-Type: application/json
       {"questions": [1,2,3,10], "answers": [1,0,0,1]}

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: application/json
       {"status": 200}

    :<json list questions: List of questions IDs with answers.
    :<json list answers: List of answers for the `questions`; 0 - false,
        1 - true. *Number of answers must be the same as questions.*

    :>json int status: Response status.

    :statuscode 200: Everything is ok.
    :statuscode 401: Login required.
    :statuscode 403: See **access**.
    :statuscode 400: Not a JSON. Client sent malformed JSON string.
    :statuscode 400: Missing parameter. At least one of the parameters missing.
    :statuscode 400: Parameters length mismatch.
        Lists has different numbers of elements.
    :statuscode 400: Empty list.
    :statuscode 400: Invalid value. List element is not a number.
    """
    user_id = get_user_id()
    data = request.get_json(force=True)
    try:
        id_list = data['questions']
        answers = data['answers']
    except KeyError:
        raise BadRequest('Missing parameter.')
    app.core.saveErrorReview(session['quiz_id'], user_id, id_list, answers)
    return json_response()


@api.route('/exam')
@access.be_client_or_guest.require()
@count_user_access()
def create_exam():
    """Get exam for the user.
    The exam will expire after **3 hrs** since creation.

    **Access**: student, guest.

    **Example requests**:

    .. sourcecode:: http

      GET /exam HTTP/1.1

    .. sourcecode:: http

      GET /exam?lang=de HTTP/1.1

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: application/json

       {
         "status": 200,
         "exam": {
           "id": 9,
           "expires": "2013-03-14 18:11:21"
         },
         "questions": [
           {
             "answer": 0,
             "text": "Question text1",
             "image": 234,
             "id": 12
           }
         ]
       }

    :query lang: Questions language, default is *it*.

    :>json int status: Response status.
    :>json dict exam: Exam metadata.
    :>json int exam.id: Exam metadata.
    :>json string exam.expired: Expiration time of the exam (time in UTC).
        After this time the Service will not accept exam answers.
    :>json list questions: List of exam questions.
        See :http:get:`/v1/quiz/(int:topic)`.

    :statuscode 200: Everything is ok.
    :statuscode 401: Login required.
    :statuscode 403: See **access**.
    """
    user_id = get_user_id()
    lang = request.args.get('lang', 'it')
    exam_type = request.args.get('exam_type', None)
    if session['quiz_name'] == 'cqc' and exam_type is None:
        raise BadRequest('Invalid exam type.')
    exam = app.core.createExam(session['quiz_id'], user_id, lang, exam_type)
    return dict_to_json_response(exam)


@api.route('/exam/<int:id>', methods=['POST'])
@access.be_client_or_guest.require()
@count_user_access()
def save_exam(id):
    """Send answers for the specified exam.
    Client sends list of answered questions and answers.
    List of questions/answers is fixed to 40.

    **Access**: student, guest.

    **Example request**:

    .. sourcecode:: http

       POST /exam/9 HTTP/1.1
       Content-Type: application/json
       {"questions": [1,2,3,10], "answers": [1,0,0,1]}

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: application/json
       {"status": 200}

    :arg id: ID of the exam.

    :<json list questions: List of exam questions.
    :<json list answers: List of exam answers.
        *Number of answers must be the same as questions.*

    :>json int status: Response status.

    :statuscode 200: Everything is ok.
    :statuscode 401: Login required.
    :statuscode 403: See **access**.
    :statuscode 400: Not a JSON. Client sent malformed JSON string.
    :statuscode 400: Missing parameter. At least one of the parameters missing.
    :statuscode 400: Parameters length mismatch.
        Lists has different numbers of elements.
    :statuscode 400: Wrong number of answers. There must be 40 answers.
    :statuscode 400: Invalid exam ID.
    :statuscode 400: Invalid value. List element is not a number.
    :statuscode 400: Exam is already passed.
    :statuscode 400: Exam is expired.
    :statuscode 400: Invalid question ID.
    """
    data = request.get_json(force=True)
    try:
        questions = data['questions']
        answers = data['answers']
    except KeyError:
        raise BadRequest('Missing parameter.')
    num_errors = app.core.saveExam(id, questions, answers)
    return json_response(num_errors=num_errors)


@api.route('/exam/<int:id>')
@access.be_user.require()
@count_user_access()
def get_exam_info(id):
    """Get information about specified exam.

    **Access**: school, student, guest.

    **Example requests**:

    .. sourcecode:: http

       GET /exam/9 HTTP/1.1

    .. sourcecode:: http

       GET /exam/9?lang=fr HTTP/1.1

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: application/json

       {
         "status": 200,
         "student": {
           "id": 42,
           "name": "Chuck",
           "surname": "Norris"
         },
         "exam": {
           "id": 1,
           "start": "2013-03-19 17:16:00",
           "end": "2013-03-19 17:16:00",
           "errors": 2,
           "status": "passed"
         },
         "questions": [
           {
             "answer": 1,
             "text": "Question text2",
             "image": 34,
             "id": 3,
             "image_bis": "b",
             "is_correct": 1
           }
         ]
       }

    :arg id: ID of the exam.

    :query lang: Questions language, default is *it*.

    :>json int status: Response status.

    :>json dict student: Client account metadata.
    :>json int student.id: Account ID.
    :>json string student.name: Account name.
    :>json string student.surname: Account surname.

    :>json dict exam: Exam metadata.
    :>json int exam.id: Exam ID.
    :>json string exam.start: Start date & time (UTC).
    :>json string exam.end: End date & time (UTC).
    :>json string exam.errors: Number of errors.
    :>json string exam.status: Exam status:
        failed, passed, expired, in-progress.

    :>json dict questions: List of exam questions with answer status.
        See :http:get:`/v1/quiz/(int:topic)`.
    :>json int questions.is_correct: Answer status, 0 - incorrect, 1 - correct.

    :statuscode 200: Everything is ok.
    :statuscode 401: Login required.
    :statuscode 403: See **access**.
    :statuscode 400: Invalid exam ID.
    """
    lang = request.args.get('lang', 'it')
    info = app.core.getExamInfo(id, lang)
    user_id = info['student']['id']
    school_id = info['student']['school_id']

    # School can access to exams of it's students only.
    if current_user.is_school and not OwnerPermission(school_id).can():
        abort(403)
    # Students can access only to their own exams.
    elif current_user.is_school_member and not OwnerPermission(user_id).can():
        abort(403)

    return dict_to_json_response(info)


@api.route('/student/<uid:user>/exam')
@access.be_user.require()
@count_user_access()
def get_student_exams(user):
    """Get exam list for the student with specified ID.
    If ``user`` is *me* then current user id is used.

    **Access**: school, student, guest.

    **Example requests**:

    .. sourcecode:: http

       GET /student/1 HTTP/1.1

    .. sourcecode:: http

       GET /student/me HTTP/1.1

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: application/json

       {
         "status": 200,
         "student": {
           "id": 42,
           "name": "Chuck",
           "surname": "Norris"
         },
         "exams": {
           "current": [
               {
                 "id": 1,
                 "start": "2013-03-29 07:12:11",
                 "end": "2013-03-29 07:20:00",
                 "errors": 5,
                 "status": "failed"
               },
               {
                 "id": 2,
                 "start": "2013-03-29 07:25:11",
                 "end": "None",
                 "errors": 0,
                 "status": "expired"
               },
               {
                 "id": 3,
                 "start": "2013-03-29 11:12:42",
                 "end": "None",
                 "errors": 0,
                 "status": "in-progress"
               }
             ],
           "week": [],
           "week3": []
         }
       }

    :arg user: Student ID.

    :>json int status: Response status.
    :>json dict student: Client account metadata.
    :>json int student.id: Account ID.
    :>json string student.name: Account name.
    :>json string student.surname: Account surname.
    :>json dict exams: Exams statistics.
    :>json list exams.current: List of today exams.
    :>json list exams.week: List of last week exams.
    :>json list exams.week3: List of exams for 7 weeks before last week.
        *[3 weeks ago; 8 weeks ago].* See :http:get:`/v1/exam/(int:id)`.

    :statuscode 200: Everything is ok.
    :statuscode 401: Login required.
    :statuscode 403: See **access**.
    :statuscode 400: Unknown student.
    :statuscode 400: Not a student: given user is not a student.
    """
    user_id = get_user_id(user)

    # Fast check to prevent extra query if access is denied.
    # For school we check if it doesn't ask with 'me' ID
    # and for student we check if he has the same ID.
    if ((current_user.is_school and user == 'me') or
        (current_user.is_school_member and not OwnerPermission(user_id))):
        abort(403)

    exams = app.core.getExamList(session['quiz_id'], user_id)
    school_id = exams['student']['school_id']

    # School can access to exams of it's students only.
    if current_user.is_school and not OwnerPermission(school_id).can():
        abort(403)
    return dict_to_json_response(exams)


@api.route('/student/<uid:user>/topicerrors/<int:id>')
@access.be_user.require()
@count_user_access()
def get_topic_error(user, id):
    """Get questions with wrong answers for the specified topic.

    **Access**: school, student, guest.

    **Example requests**:

    .. sourcecode:: http

       GET /student/me/topicerrors/12 HTTP/1.1

    .. sourcecode:: http

       GET /student/12/topicerrors/1?lang=fr HTTP/1.1

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: application/json

       {
         "status": 200,
         "student": {
           "id": 42,
           "name": "Chuck",
           "surname": "Norris"
         },
         "questions": [
           {
             "answer": 0,
             "text": "Question text1",
             "image": 234,
             "id": 12
           },
         ]
       }

    :arg user: Student ID.
    :arg id: Topic ID for which questions are requested.

    :query lang: Questions language, default is *it*.

    :>json int status: Response status.
    :>json dict student: Client account metadata.
    :>json int student.id: Account ID.
    :>json string student.name: Account name.
    :>json string student.surname: Account surname.
    :>json list questions: Questions with wrong answers.
        See :http:get:`/v1/exam/(int:id)`.

    :statuscode 200: Everything is ok.
    :statuscode 401: Login requires.
    :statuscode 403: See **access**.
    """
    user_id = get_user_id(user)
    lang = request.args.get('lang', 'it')

    # Fast check to prevent extra query if access is denied.
    # For school we check if it doesn't ask with 'me' ID
    # and for student we check if he has the same ID.
    if ((current_user.is_school and user == 'me') or
        (current_user.is_school_member and not OwnerPermission(user_id))):
        abort(403)

    info = app.core.getTopicErrors(session['quiz_id'], user_id, id, lang)
    school_id = info['student']['school_id']

    # School can access to info of it's students only.
    if current_user.is_school and not OwnerPermission(school_id).can():
        abort(403)

    return dict_to_json_response(info)


# TODO: do we need this call?
@api.route('/admin/schools')
@access.be_admin.require()
def school_list():
    res = app.account.getSchools()
    return dict_to_json_response(res)


# TODO: do we need this call?
@api.route('/admin/newschool', methods=['POST'])
@access.be_admin.require()
def add_school():
    res = app.account.addSchool(raw=request.data)
    return dict_to_json_response(res)


# TODO: do we need this call?
@api.route('/admin/school/<int:id>', methods=['POST', 'DELETE'])
@access.be_admin.require()
def delete_school(id):
    if request.method == 'POST':
        action = request.args.get('action', None)
        if action != 'delete':
            raise BadRequest('Invalid action.')
        elif len(request.data):
            raise BadRequest('Invalid request.')

    res = app.account.removeSchool(id)

    if res['status'] == 200:
        res = app.core.deleteSchool(id)
    return dict_to_json_response(res)


# Note: we don't check school permissions since accounts service will do it.
@api.route('/school/<uid:id>/students')
@access.be_admin_or_school.require()
def student_list(id):
    """Get list of students for the given school.
    If ``id`` is *me* then school id will be retrieved from the session.

    **Access**: school, admin.

    **Example requests**:

    .. sourcecode:: http

       GET /school/me/students HTTP/1.1

    .. sourcecode:: http

       GET /school/1/students HTTP/1.1

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: application/json

       {
         "status": 200,
         "students": [
           {
             "id": 2,
             "name": "Chuck Norris School",
             "surname": "",
             "login": "chuck@norris.com-guest",
             "type": "guest",
           }
         ]
       }

    :arg id: School ID.

    :>json int status: Response status.
    :>json list students: List of school's students.
    :>json int students.id: Account ID.
    :>json string students.name: Account name.
    :>json string students.surname: Account surname.
    :>json string students.login: Account login.
    :>json string students.type: Account type: student, guest.

    :statuscode 200: Everything is ok.
    :statuscode 401: Login required.
    :statuscode 403: See **access**.
    :statuscode 400: Invalid school ID.

    .. note::
        It sends request to the **Accounts Service**.
    """
    school_id = get_user_id(id)
    res = app.account.getSchoolStudents(school_id)
    return dict_to_json_response(res)


# Note: we don't check school permissions since accounts service will do it.
@api.route('/school/<uid:id>/newstudent', methods=['POST'])
@access.be_admin_or_school.require()
def add_student(id):
    """Create new student for the given school.
    If ``id`` is *me* then school id will be retrieved from the session.

    **Example requests**:

    .. sourcecode:: http

       POST /school/12/newstudent HTTP/1.1
       Content-Type: application/json

       {
         "name": "Chuck Norris",
         "surname": "Son",
         "login": "chuck.jr@norris.com",
         "passwd": "32bfe1c505d4a2a042bafd53993f10ece3ccddca",
       }

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: application/json

       {
         "status": 200,
         "id": 42,
         "name": "Chuck Norris",
         "surname": "Son"
       }

    :arg id: School ID.

    :<json string name: New student name.
    :<json string surname: New student surname.
    :<json string login: New student login.
    :<json string passwd: New student password hash (see note).

    :>json int status: Response status.
    :>json int id: New student ID.
    :>json string name: New student name.
    :>json string surname: New student surname.

    :statuscode 200: Everything is ok.
    :statuscode 401: Login required.
    :statuscode 403: See **access**.
    :statuscode 400: Missing parameter.
    :statuscode 400: Invalid parameters.
    :statuscode 400: Already exists. Student with the same login is
        already exists.
    :statuscode 400: Invalid school ID.

    .. note::
        ``passwd`` formula::

            passwd = MD5(login:password)
    """
    school_id = get_user_id(id)
    res = app.account.addStudent(school_id, raw=request.data)
    return dict_to_json_response(res)


# Note: we don't check school permissions since accounts service will do it.
@api.route('/school/<uid:id>/student/<int:student>', methods=['POST', 'DELETE'])
@access.be_admin_or_school.require()
def delete_student(id, student):
    """Delete specified student from the given school.
    If ``id`` is *me* then school id will be retrieved from the session.

    **Access**: school.

    **Example requests**:

    .. sourcecode:: http

       POST /school/me/student/10?action=delete HTTP/1.1

    .. sourcecode:: http

       DELETE /school/me/student/10 HTTP/1.1

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: application/json
       {"status": 200}

    :arg id: School ID.
    :arg student: Student ID.

    :>json int status: Response status.

    :statuscode 200: Everything is ok.
    :statuscode 401: Login required.
    :statuscode 403: See **access**.
    :statuscode 400: Invalid school ID.
    :statuscode 400: Unknown student.
    :statuscode 400: Invalid action.

    .. note::
        All student's data will be removed too.

    .. note::
        It sends request to the **Accounts Service**.
    """
    if request.method == 'POST':
        action = request.args.get('action', None)
        if action != 'delete':
            raise BadRequest('Invalid action.')
        elif len(request.data):
            raise BadRequest('Invalid request.')

    id = get_user_id(id)
    res = app.account.removeStudent(student)

    # Remove student from local DB if he was removed from accounts.
    if res['status'] == 200:
        app.core.deleteStudent(student)

    return dict_to_json_response(res)


@api.route('/school/<uid:id>')
@access.be_admin_or_school.require()
def school_stat(id):
    """Get statistics for the given school.
    If ``id`` is *me* then school id will be retrieved from the session.

    **Access**: school, admin.

    **Example request**:

    .. sourcecode:: http

       GET /v1/school/1 HTTP/1.1

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: application/json

       {
         "status": 200,
         "guest_visits": [30,20,-1],
         "exams": [4,20,33],
         "topics": [
           {
             "id": 1,
             "text": "Topic 1",
             "errors": {
               "current": 12,
               "week": 34.5,
               "week3": -1
             }
           }
         ],
         "students": {
           "current": {
             "worst": [
               {
                 "id": 1,
                 "name": "Chuck",
                 "surname": "Norris",
                 "coef": 0.45
               },
             ],
             "best": []
           },
           "week": {"worst": [], "best": []},
           "week3": {"worst": [], "best": []}
         }
       }

    :arg id: School ID.

    :query lang: Topics language, default is *it*.

    :>json int status: Response status.
    :>json list guest_visits: List of quest visits [current, week, week3].
    :>json list exams: List of exams errors [current, week, week3].

    :>json list topics: List of topics statistics.
    :>json int topics.id: Topic ID.
    :>json string topics.text: Topic title.
    :>json dict topics.errors: Topic errors statistics. ``-1`` means no data.

    :>json dict students: School's students statistics.
    :>json dict students.current: Today stat.
    :>json list students.current.worst: List of worst students.
    :>json list students.current.best: List of best students.
    :>json dict students.week: Same as ``students.current`` for for last week.
    :>json dict students.week3: Same as ``students.current`` for for 7 weeks
        before last week.

    :statuscode 200: Everything is ok.
    :statuscode 401: Login required.
    :statuscode 403: See **access**.
    :statuscode 400: Invalid school ID.
    """
    def _get_ids(data):
        if 'best' not in data or 'worst' not in data:
            return []
        return [x['id'] for x in data['best']] + [x['id'] for x in data['worst']]

    def _update_names(users, data):
        for x in data:
            user = users[x['id']]
            x['name'] = user['name']
            x['surname'] = user['surname']

    school_id = get_user_id(id)

    if current_user.is_school:
        if not OwnerPermission(school_id).can():
            abort(403)
    elif id == 'me':
        abort(403)

    lang = request.args.get('lang', 'it')
    res = app.core.getSchoolStat(session['quiz_id'], school_id, lang)

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

    return dict_to_json_response(res)


# NOTE: this call is for internal use by accounts service.
@api.route('/stat/school_exams')
def stat_school_exams():
    # It returns raw string with json content;
    # and we simply resend it to the caller as JSON response.
    stat = app.core.getStatByExams()
    result = stat or '{}'
    r = app.response_class(result, mimetype='application/json')
    return r


@api.route('/accept_cookie')
@access.be_user.require()
def accept_cookie():
    student_id = current_user.account['id']
    res = app.account.acceptStudentCookie(student_id)
    current_user.account['cookie'] = 1
    return dict_to_json_response({"status": res.status_code})
