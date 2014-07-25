from functools import wraps
from werkzeug.exceptions import BadRequest
from werkzeug.urls import url_encode, Href
from flask import current_app as app
from flask import Blueprint, request, session, Response, redirect, abort
from .appcore import json_response, dict_to_json_response
from .core.exceptions import QuizCoreError
from . import access
from .access import current_user, OwnerPermission

api = Blueprint('api', __name__)


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
                quiz_type = session['quiz_type']
                sid = user.account['school_id']
                uid = user.account_id
                user_type = user.user_type
                app.core.updateUserLastVisit(quiz_type, uid, user_type, sid)
                if handle_guest and user.is_guest:
                    if not app.core.processGuestAccess(quiz_type, uid):
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
# kb.imakewebsites.ca/2013/04/30/safari-3rd-party-cookies-and-facebook-apps/
# NOTE: beaker sessions dependent solution!
@api.route('/ifix')
def iframe_fix():
    next_url = request.args.get('next')
    session['ensure_session'] = True  # to have 'cookie_out' in session.
    if next_url is None:
        raise BadRequest('Missing argument.')
    r = Response(_ifix_html.format(next_url), mimetype='text/html')
    r.headers['Set-Cookie'] = session._headers['cookie_out']
    return r


@api.route('/accounturl')
def get_account_url():
    url, cid = app.account.getUserAccountPage()
    args = request.args.copy()
    args['cid'] = cid
    return redirect(url + '?' + url_encode(args))


@api.route('/userinfo')
def get_authorize_status():
    info = app.account.getUserInfo()
    return dict_to_json_response(info)


@api.route('/fbcanvas/<path>/', methods=['GET', 'POST'])
def fb_canvas(path):
    hr = Href(request.host_url + path + '/')
    args = request.args.copy()
    args['fblogin'] = 1
    return redirect(hr(args))


@api.route('/link_facebook', methods=['POST'])
@access.be_client.require()
@count_user_access()
def link_facebook():
    data = request.get_json(force=True)
    try:
        user_id = data['userId']
    except KeyError:
        raise BadRequest('Missing parameter.')
    res = app.account.linkFacebookAccount(user_id)
    return dict_to_json_response(res)


@api.route('/quiz/<int:topic>')
@access.be_client_or_guest.require()
@count_user_access()
def create_quiz(topic):
    """ Get 40 questions from the DB and return them to the client."""
    user_id = get_user_id()
    lang = request.args.get('lang', 'it')
    force = request.args.get('force', False)
    exclude = request.args.get('exclude', None)
    if exclude is not None:
        try:
            exclude = exclude.split(',')
            exclude = [int(x) for x in exclude]
        except ValueError:
            raise QuizCoreError('Invalid parameters.')
    quiz = app.core.getQuiz(session['quiz_type'], user_id, topic, lang, force,
                            exclude)
    return dict_to_json_response(quiz)


@api.route('/quiz/<int:topic>', methods=['POST'])
@access.be_client_or_guest.require()
@count_user_access()
def save_quiz(topic):
    """ Save quiz results."""
    user_id = get_user_id()
    data = request.get_json(force=True)
    try:
        id_list = data['questions']
        answers = data['answers']
    except KeyError:
        raise BadRequest('Missing parameter.')
    app.core.saveQuiz(session['quiz_type'], user_id, topic, id_list, answers)
    return json_response()


@api.route('/student', defaults={'user': 'me'})
@api.route('/student/<uid:user>')
@access.be_user.require()
@count_user_access()
def get_student_stat(user):
    user_id = get_user_id(user)  # requested user
    lang = request.args.get('lang', 'it')
    stat = app.core.getUserStat(session['quiz_type'], user_id, lang)

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
    user_id = get_user_id()
    lang = request.args.get('lang', 'it')
    exclude = request.args.get('exclude', None)
    if exclude is not None:
        try:
            exclude = exclude.split(',')
            exclude = [int(x) for x in exclude]
        except ValueError:
            raise QuizCoreError('Invalid parameters.')
    res = app.core.getErrorReview(session['quiz_type'], user_id, lang, exclude)
    return dict_to_json_response(res)


@api.route('/errorreview', methods=['POST'])
@access.be_client_or_guest.require()
@count_user_access()
def save_error_review():
    user_id = get_user_id()
    data = request.get_json(force=True)
    try:
        id_list = data['questions']
        answers = data['answers']
    except KeyError:
        raise BadRequest('Missing parameter.')
    app.core.saveErrorReview(session['quiz_type'], user_id, id_list, answers)
    return json_response()


@api.route('/exam')
@access.be_client_or_guest.require()
@count_user_access()
def create_exam():
    user_id = get_user_id()
    lang = request.args.get('lang', 'it')
    exam_type = request.args.get('exam_type', None)
    if session['quiz_type_name'] == 'cqc' and exam_type is None:
        raise BadRequest('Invalid exam type.')
    exam = app.core.createExam(session['quiz_type'], user_id, lang, exam_type)
    return dict_to_json_response(exam)


@api.route('/exam/<int:id>', methods=['POST'])
@access.be_client_or_guest.require()
@count_user_access()
def save_exam(id):
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
    user_id = get_user_id(user)

    # Fast check to prevent extra query if access is denied.
    # For school we check if it doesn't ask with 'me' ID
    # and for student we check if he has the same ID.
    if ((current_user.is_school and user == 'me') or
        (current_user.is_school_member and not OwnerPermission(user_id))):
        abort(403)

    exams = app.core.getExamList(session['quiz_type'], user_id)
    school_id = exams['student']['school_id']

    # School can access to exams of it's students only.
    if current_user.is_school and not OwnerPermission(school_id).can():
        abort(403)
    return dict_to_json_response(exams)


@api.route('/student/<uid:user>/topicerrors/<int:id>')
@access.be_user.require()
@count_user_access()
def get_topic_error(user, id):
    user_id = get_user_id(user)
    lang = request.args.get('lang', 'it')

    # Fast check to prevent extra query if access is denied.
    # For school we check if it doesn't ask with 'me' ID
    # and for student we check if he has the same ID.
    if ((current_user.is_school and user == 'me') or
        (current_user.is_school_member and not OwnerPermission(user_id))):
        abort(403)

    info = app.core.getTopicErrors(session['quiz_type'], user_id, id, lang)
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
    school_id = get_user_id(id)
    res = app.account.getSchoolStudents(school_id)
    return dict_to_json_response(res)


# Note: we don't check school permissions since accounts service will do it.
@api.route('/school/<uid:id>/newstudent', methods=['POST'])
@access.be_admin_or_school.require()
def add_student(id):
    school_id = get_user_id(id)
    res = app.account.addStudent(school_id, raw=request.data)
    return dict_to_json_response(res)


# Note: we don't check school permissions since accounts service will do it.
@api.route('/school/<uid:id>/student/<int:student>', methods=['POST', 'DELETE'])
@access.be_admin_or_school.require()
def delete_student(id, student):
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
    res = app.core.getSchoolStat(session['quiz_type'], school_id, lang)

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
