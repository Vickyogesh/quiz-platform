import hashlib
from werkzeug.exceptions import HTTPException
from flask import redirect, url_for, flash, request, session, abort
from flask_wtf import Form
from flask_login import current_user
from wtforms import StringField, PasswordField, HiddenField
from . import ui
from .babel import lazy_gettext, gettext
from .util import render_template
from .. import app, access
from ..login import QUIZ_ID_MAP, do_login, quiz_name_parts


def after_login():
    """Redirect to menu page or to the page specified in the URL query
    parameter 'next'.
    """
    next_url = request.args.get('next')

    # This part if needed for integration with CMS service.
    # Later these dta will be used in exam to post to Facebook feed.
    # See ExamView.postOnFacebook() in js/exam-view.js and Exam in client.py.
    extra_school_name = request.args.get('n')
    extra_school_url = request.args.get('nu')
    extra_school_logo_url = request.args.get('nl')
    if extra_school_name is not None:
        session['extra_school_name'] = extra_school_name
        session['extra_school_url'] = extra_school_url
        session['extra_school_logo_url'] = extra_school_logo_url

    if next_url is not None:
        return redirect(next_url)
    else:
        if access.current_user.is_school:
            return redirect(url_for('.school_menu'))
        else:
            return redirect(url_for('.client_menu'))


class LoginFrom(Form):
    name = StringField(lazy_gettext('Login'))
    pwd = PasswordField(lazy_gettext('Password'))
    fb_auth_id = HiddenField()
    fb_auth_token = HiddenField()
    is_fb = HiddenField()


def get_plain_login(login, passwd, quiz_fullname):
    nonce = app.account.get_auth().get('nonce', '')
    digest = hashlib.md5('{0}:{1}'.format(login, passwd)).hexdigest()
    digest = hashlib.md5('{0}:{1}'.format(nonce, digest)).hexdigest()
    return {
        'nonce': nonce,
        'login': login,
        'appid': '32bfe1c505d4a2a042bafd53993f10ece3ccddca',
        'quiz_type': quiz_fullname,
        'digest': digest
    }


def get_fb_login(fb_id, fb_auth_token, quiz_fullname):
    return {
        'appid': '32bfe1c505d4a2a042bafd53993f10ece3ccddca',
        'quiz_type': quiz_fullname,
        'fb': {
            'id': fb_id,
            'token': fb_auth_token
        }
    }


@ui.route('/', defaults={'quiz_fullname': 'b2013'}, methods=['GET', 'POST'])
@ui.route('/<quiz_fullname>', methods=['GET', 'POST'])
def index(quiz_fullname):
    if quiz_fullname not in QUIZ_ID_MAP:
        abort(404)

    # Skip login for already signed users (for the given quiz).
    if current_user.is_authenticated() and (current_user.is_school
                                            or current_user.is_school_member):
        if session['quiz_fullname'] == quiz_fullname:
            return after_login()

    fb_autologin = request.args.get('fblogin')
    form = LoginFrom()
    if form.validate_on_submit():
        if form.is_fb.data == "1":
            fb_id = form.fb_auth_id.data
            fb_auth_token = form.fb_auth_token.data
            data = get_fb_login(fb_id, fb_auth_token, quiz_fullname)
        else:
            login = form.name.data
            passwd = form.pwd.data
            data = get_plain_login(login, passwd, quiz_fullname)

        try:
            do_login(data)
        except HTTPException as e:
            fb_autologin = None
            if e.code == 403:
                flash(gettext('Forbidden.'))
            else:
                flash(e.description)
        else:
            return after_login()

    quiz_name, _, _ = quiz_name_parts(quiz_fullname)
    return render_template('ui/index.html', form=form,
                           quiz_fullname=quiz_fullname,
                           quiz_name=quiz_name,
                           fb_autologin=fb_autologin)


@ui.route('/logout')
@access.login_required
def logout():
    quiz_fullname = session['quiz_fullname']
    access.logout()
    return redirect(url_for('.index', quiz_fullname=quiz_fullname))
