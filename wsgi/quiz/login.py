from datetime import datetime
from werkzeug.exceptions import BadRequest, Forbidden
from flask import current_app as app
from flask import request, session, Blueprint
from .core.exceptions import QuizCoreError
from .appcore import json_response
from . import access

QUIZ_TYPE_ID = {
    'b2011': 1,
    'cqc': 2,
    'b2013': 3
}

login_api = Blueprint('login_api', __name__)


def _get_quiz_type(quiz_name):
    return QUIZ_TYPE_ID.get(quiz_name, None)


# Raises error if access is denied or returns expiration date.
def _validate_quiz_access(quiz_type, quiz_type_id, user):
    access = user['access']
    date_str = access.get(quiz_type, None)
    if not date_str:
        raise Forbidden('Forbidden.')

    # Convert string to date.
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise BadRequest('Unexpected account data.')

    now = datetime.utcnow().date()
    if d < now:
        raise Forbidden('Forbidden.')
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


@login_api.route('/authorize', methods=['GET'])
def ask_login():
    data = app.account.get_auth()
    return json_response(status=401, nonce=data['nonce'])


@login_api.route('/authorize', methods=['POST'])
def login():
    data = request.get_json(force=True)

    # handle facebook login
    if 'fb' in data:
        appid, (user, cookie) = _facebook_login(data)
    else:
        appid, (user, cookie) = _plain_login(data)

    can_check_date = user['type'] != 'admin'

    try:
        quiz_type = data["quiz_type"]
    except KeyError:
        raise BadRequest('Invalid parameters.')

    quiz_type_id = _get_quiz_type(quiz_type)
    if quiz_type_id is None:
        raise BadRequest('Invalid parameters.')

    if can_check_date:
        end_date = _validate_quiz_access(quiz_type, quiz_type_id, user)

    # Used by API to detect current quiz.
    session['quiz_type'] = quiz_type_id
    session['quiz_type_name'] = quiz_type

    if can_check_date:
        session['access_end_date'] = end_date
    session['app_id'] = appid
    access.login(user)

    # NOTE: we you want to use 'beaker.session.secret' then use:
    # sid = self.session.__dict__['_headers']['cookie_out']
    # sid = sid[sid.find('=') + 1:sid.find(';')]
    # sid = self.session.id

    return json_response(user=user)


@login_api.route('/authorize/logout', methods=['GET', 'POST'])
@access.login_required
def logout():
    access.logout()
    return json_response()
