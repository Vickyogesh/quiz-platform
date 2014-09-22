from datetime import datetime
from werkzeug.exceptions import BadRequest
from flask import current_app as app
from flask import request, session, Blueprint, abort
from .core.exceptions import QuizCoreError
from .appcore import json_response
from . import access

QUIZ_ID_MAP = {
    'b2011': 1,
    'cqc': 2,
    'b2013': 3,
    'scooter': 4
}

login_api = Blueprint('login_api', __name__)


def first_digit_index(txt):
    """Return index of the first digit in the given string."""
    index = -1
    for x in txt:
        index += 1
        if x.isdigit():
            return index
    return -1


def quiz_name_parts(quiz_name):
    """Split given quiz name in to parts: name[year[.version]].

    Returns:
        tuple(name, year, version)
    """
    basename = quiz_name
    year = None
    version = None
    index = first_digit_index(quiz_name)
    if index != -1:
        basename = quiz_name[:index]
        year = quiz_name[index:]
        index = year.find('.')
        if index != -1:
            version = year[index + 1:]
            year = year[:index]
        try:
            year = year and int(year)
            version = version and int(version)
        except ValueError:
            basename = quiz_name
            year = None
            version = None
    return basename, year, version


def _get_quiz_id(quiz_name):
    return QUIZ_ID_MAP.get(quiz_name, None)


# Raises error if access is denied or returns expiration date.
def _validate_quiz_access(quiz_name, quiz_id, user):
    access = user['access']
    date_str = access.get(quiz_name, None)
    if not date_str:
        abort(403)
    # Convert string to date.
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise BadRequest('Unexpected account data.')

    now = datetime.utcnow().date()
    if d < now:
        abort(403)
    else:
        return d


def _plain_login(data):
    try:
        nonce = data["nonce"]
        login = data["login"]
        appkey = data["appid"]
        digest = data["digest"]
    except KeyError:
        raise BadRequest('Invalid parameters.')

    try:
        appid = app.core.getAppId(appkey)
    except QuizCoreError:
        raise BadRequest('Authorization is invalid.')

    return appid, app.account.send_auth(login, digest, nonce, 'quiz')


def _facebook_login(data):
    try:
        fb_id = data['fb']['id']
        fb_token = data['fb']['token']
        appkey = data['appid']
    except KeyError:
        raise BadRequest('Invalid parameters.')

    try:
        appid = app.core.getAppId(appkey)
    except QuizCoreError:
        raise BadRequest('Authorization is invalid.')

    return appid, app.account.send_fb_auth(fb_id, fb_token, 'quiz')


def do_login(data):
    # handle facebook login
    if 'fb' in data:
        appid, (user, cookie) = _facebook_login(data)
    else:
        appid, (user, cookie) = _plain_login(data)

    can_check_date = user['type'] != 'admin'

    try:
        quiz_fullname = data["quiz_type"]
    except KeyError:
        raise BadRequest('Invalid parameters.')

    quiz_id = _get_quiz_id(quiz_fullname)
    if quiz_id is None:
        raise BadRequest('Invalid parameters.')

    if can_check_date:
        end_date = _validate_quiz_access(quiz_fullname, quiz_id, user)

    # Used by API to detect current quiz.
    basename, year, version = quiz_name_parts(quiz_fullname)
    session['quiz_name'] = basename
    session['quiz_year'] = year
    session['quiz_version'] = version
    session['quiz_fullname'] = quiz_fullname
    session['quiz_id'] = quiz_id

    if can_check_date:
        session['access_end_date'] = end_date
    session['app_id'] = appid
    access.login(user)
    # NOTE: we you want to use 'beaker.session.secret' then use:
    # sid = self.session.__dict__['_headers']['cookie_out']
    # sid = sid[sid.find('=') + 1:sid.find(';')]
    # sid = self.session.id
    return user


@login_api.route('/authorize', methods=['GET'])
def ask_login():
    data = app.account.get_auth()
    return json_response(status=401, nonce=data['nonce'])


@login_api.route('/authorize', methods=['POST'])
def login():
    data = request.get_json(force=True)
    user = do_login(data)
    return json_response(user=user)


@login_api.route('/authorize/logout', methods=['GET', 'POST'])
@access.login_required
def logout():
    access.logout()
    return json_response()
