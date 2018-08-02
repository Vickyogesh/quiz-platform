from datetime import datetime, timedelta
import hashlib
from werkzeug.exceptions import BadRequest
from itsdangerous import BadSignature
from flask import current_app as app
from flask import request, session, Blueprint, abort, g
from .core.exceptions import QuizCoreError
from .appcore import json_response
from . import access

QUIZ_ID_MAP = {
    'b2011': 1,
    'b2013': 3,
    'b2016': 50,
    'cqc': 2,
    'am': 4,
    # (it covers 7 sub types 5 - 11), see quiz_cde
    'cde': 5,

    #  covers 60-66, see quiz_rev/data.py
    'revisioni': 60
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
        digest_old = data.get("digest_old")
    except KeyError:
        raise BadRequest('Invalid parameters.')

    try:
        appid = app.core.getAppId(appkey)
    except QuizCoreError:
        raise BadRequest('Authorization is invalid.')

    return appid, app.account.send_auth(login, digest, digest_old, nonce, 'quiz')


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

    app_id = app.config['FACEBOOK_APP_ID']
    secret = app.config['FACEBOOK_APP_SECRET']
    return appid, app.account.send_fb_auth(fb_id, fb_token, 'quiz',
                                           app_id=app_id, secret=secret)


def do_login(data, remember=False):
    # handle facebook login
    if 'fb' in data:
        appid, (user, cookie) = _facebook_login(data)
    else:
        appid, (user, cookie) = _plain_login(data)
        # used for remember me tocken, see access.User.get_auth_token()
        user['passwd'] = data.get('passwd')

    if user['type'] == 'content_manager':
        user['access'] = {}
        user['quiz'] = None
        access.login(user, remember)
        return user

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
    access.login(user, remember)
    # NOTE: we you want to use 'beaker.session.secret' then use:
    # sid = self.session.__dict__['_headers']['cookie_out']
    # sid = sid[sid.find('=') + 1:sid.find(';')]
    # sid = self.session.id
    return user


def get_plain_login(login, passwd, quiz_fullname):
    login = login.encode('utf-8')
    passwd = passwd.encode('utf-8')

    nonce = app.account.get_auth().get('nonce', '')
    # for old users
    digest_old = hashlib.md5('{0}:{1}'.format(login, passwd)).hexdigest()
    digest_old = hashlib.md5('{0}:{1}'.format(nonce, digest_old)).hexdigest()
    # for new
    digest = hashlib.md5('{0}:{1}'.format(app.config['SALT'], passwd)).hexdigest()
    digest = hashlib.md5('{0}:{1}'.format(nonce, digest)).hexdigest()
    return {
        'nonce': nonce,
        'login': login,
        'appid': '32bfe1c505d4a2a042bafd53993f10ece3ccddca',
        'quiz_type': quiz_fullname,
        'digest': digest,
        'digest_old': digest_old,
        'passwd': passwd
    }


# @access.login_manager.token_loader
# def token_loader(token):
#     # See BaseView.quiz_fullname
#     # Workaround to get correct full quiz name
#     def get_quiz_fullname():
#         qname = g.quiz_meta['name']
#         qyear = g.quiz_meta['year']
#         # See quiz_am.IndexView.quiz_fullname
#         if qname == 'am' and qyear == 2014:
#             return qname
#         # See quiz_cde.IndexView.quiz_fullname
#         elif qname == 'cde' and qyear == 2015:
#             return qname
#         # See quiz_cqc.IndexView.quiz_fullname
#         elif qname == 'cqc' and qyear == 2011:
#             return qname
#         return ''.join((qname, str(qyear)))
#
#     # The token itself was generated by User.get_auth_token.
#     # So it is up to us to known the format of the token data itself.
#
#     # The token was encrypted using URLSafeTimedSerializer which
#     # allows us to have a max_age on the token itself. When the cookie is stored
#     # on the users computer it also has a expiry date, but could be changed by
#     # the user, so this feature allows us to enforce the expiry date of the
#     # token server side and not rely on the users cookie to expire.
#     max_age = app.config.get('REMEMBER_COOKIE_DURATION', timedelta(days=365))
#     max_age = max_age.total_seconds()
#
#     try:
#         # Decrypt the token, data = [username, plain_passwd]
#         data = access.login_serializer.loads(token, max_age=max_age)
#         d = get_plain_login(data[0], data[1], get_quiz_fullname())
#         user = do_login(d, True)
#     except (BadSignature, BadRequest):
#         return None
#
#     return access.User(user)


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
