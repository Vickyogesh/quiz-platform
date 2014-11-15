import hashlib
from werkzeug.exceptions import HTTPException
from flask import request, current_app, flash, session, redirect, url_for
from flask_wtf import Form
from flask_babelex import lazy_gettext, gettext
from flask_login import current_user
from wtforms import StringField, PasswordField, HiddenField
from ..common.base import BaseView
from ..login import do_login


def get_plain_login(login, passwd, quiz_fullname):
    nonce = current_app.account.get_auth().get('nonce', '')
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
        # Maybe there will be fullscreen version for schools.
        # So comments are just a reminders how to implement.
        if current_user.is_school:
            return redirect(url_for('.school_menu'))
        else:
            return redirect(url_for('.client_fullscreen'))
            # return redirect(url_for('.client_menu'))


class LoginFrom(Form):
    name = StringField(lazy_gettext('Login'))
    pwd = PasswordField(lazy_gettext('Password'))
    fb_auth_id = HiddenField()
    fb_auth_token = HiddenField()
    is_fb = HiddenField()


class IndexView(BaseView):
    """Common quiz index page with login form.

    It also redirects already signed in users to corresponding pages.
    """
    methods = ['GET', 'POST']
    check_access = False
    template_name = 'index.html'
    url_rule = '/'

    def dispatch_request(self, *args, **kwargs):
        # Skip login for already signed users (for the given quiz).
        if current_user.is_authenticated() and (current_user.is_school
                                                or current_user.is_school_member):
            # See base.check_access()
            if request.args.get('reauth') != '1':
                return after_login()

        fb_autologin = request.args.get('fblogin')
        form = LoginFrom()

        if form.validate_on_submit():
            if form.is_fb.data == "1":
                fb_id = form.fb_auth_id.data
                fb_auth_token = form.fb_auth_token.data
                data = get_fb_login(fb_id, fb_auth_token, self.quiz_fullname)
            else:
                login = form.name.data
                passwd = form.pwd.data
                data = get_plain_login(login, passwd, self.quiz_fullname)

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

        fb_appid = current_app.config['FACEBOOK_APP_ID']
        return self.render_template(form=form, fb_autologin=fb_autologin,
                                    fb_appid=fb_appid)
